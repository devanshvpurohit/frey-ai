"""
FREY AI - Edge Inference Engine for Arduino UNO Q
Supports ONNX Runtime and OpenCV DNN with zero-copy CPU optimization.

Key Features:
- Universal backend: Try ONNX Runtime (CPUExecutionProvider), fallback to cv2.dnn
- Resilient tensor parsing supporting YOLO11 / YOLOv8 output shapes
- High-performance Non-Maximum Suppression (NMS)
- Letterbox image scaling to preserve foliage aspect ratio
- Detailed latency telemetry for edge performance monitoring
"""

import os
import time
import json
import logging
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import cv2

logger = logging.getLogger("frey.inference")


class InferenceEngine:
    """Manages ONNX model loading and low-level forward pass execution."""

    def __init__(
        self,
        model_path: str,
        input_size: Tuple[int, int] = (416, 416),
        conf_threshold: float = 0.25,
        nms_threshold: float = 0.45,
        num_threads: int = 4,
    ):
        self.model_path = Path(model_path)
        self.input_size = input_size
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.num_threads = num_threads

        self.backend_type: str = "none"
        self.session = None  # ONNX Runtime session or cv2.dnn Net
        self.lock = threading.Lock()
        
        self.input_name: Optional[str] = None
        self.output_names: List[str] = []
        self.is_loaded: bool = False
        
        # Telemetry
        self.last_inference_time_ms: float = 0.0
        self.total_inferences: int = 0
        self.avg_inference_time_ms: float = 0.0

        self._load_model()

    def _load_model(self):
        """Initialize inference session using ONNX Runtime or OpenCV DNN."""
        if not self.model_path.exists():
            logger.error(f"Model file not found at: {self.model_path}")
            self.is_loaded = False
            return

        # Attempt 1: ONNX Runtime
        try:
            import onnxruntime as ort
            options = ort.SessionOptions()
            options.intra_op_num_threads = self.num_threads
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=options,
                providers=["CPUExecutionProvider"]
            )
            self.backend_type = "onnxruntime"
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.is_loaded = True
            logger.info(f"Loaded {self.model_path.name} via ONNX Runtime CPU (threads={self.num_threads}).")
            return
        except ImportError:
            logger.info("ONNX Runtime not installed; attempting OpenCV DNN fallback.")
        except Exception as e:
            logger.warning(f"Failed to initialize ONNX Runtime session: {e}; attempting OpenCV DNN.")

        # Attempt 2: OpenCV DNN
        try:
            net = cv2.dnn.readNetFromONNX(str(self.model_path))
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            self.session = net
            self.backend_type = "opencv_dnn"
            self.output_names = net.getUnconnectedOutLayersNames()
            self.is_loaded = True
            logger.info(f"Loaded {self.model_path.name} via OpenCV DNN CPU.")
        except Exception as e:
            logger.error(f"Critical failure: Unable to load ONNX model via any backend: {e}")
            self.is_loaded = False

    def letterbox(
        self,
        image: np.ndarray,
        new_shape: Tuple[int, int] = (416, 416),
        color: Tuple[int, int, int] = (114, 114, 114),
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Resize and pad image while maintaining aspect ratio."""
        shape = image.shape[:2]  # [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return image, r, (dw, dh)

    def preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Prepare raw BGR frame for neural network input."""
        padded_img, ratio, (pad_w, pad_h) = self.letterbox(frame, self.input_size)
        
        # BGR -> RGB
        rgb = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
        
        # Normalize [0.0, 1.0] and CHW layout
        blob = rgb.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))  # HWC to CHW
        blob = np.expand_dims(blob, axis=0)    # Add batch dim -> BCHW
        blob = np.ascontiguousarray(blob)
        return blob, ratio, (pad_w, pad_h)

    def postprocess(
        self,
        output: np.ndarray,
        ratio: float,
        pad: Tuple[float, float],
        orig_shape: Tuple[int, int],
        conf_thresh: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Parse YOLO raw outputs, filter confidences, and apply NMS.
        
        Output format for YOLO11 is [1, 4 + num_classes, num_anchors]
        e.g. [1, 84, 3549] or [1, 33, 3549]
        """
        conf_threshold = conf_thresh if conf_thresh is not None else self.conf_threshold

        # Ensure 2D matrix [num_anchors, 4 + num_classes]
        if output.ndim == 3:
            # If shape is [1, C, N], transpose to [N, C]
            if output.shape[1] < output.shape[2]:
                output = output[0].T
            else:
                output = output[0]

        boxes = []
        confidences = []
        class_ids = []

        pad_w, pad_h = pad
        orig_h, orig_w = orig_shape

        # Extract predictions
        scores = output[:, 4:]
        max_scores = np.max(scores, axis=1)
        valid_mask = max_scores >= conf_threshold

        filtered_output = output[valid_mask]
        filtered_scores = scores[valid_mask]

        if len(filtered_output) == 0:
            return []

        best_class_ids = np.argmax(filtered_scores, axis=1)
        best_scores = np.max(filtered_scores, axis=1)

        for i in range(len(filtered_output)):
            cx, cy, w, h = filtered_output[i, :4]
            score = float(best_scores[i])
            cls_id = int(best_class_ids[i])

            # Convert center-xywh to corner coordinates in 416x416 space
            x1 = cx - (w / 2.0)
            y1 = cy - (h / 2.0)

            # Un-pad and rescale back to original camera frame coordinates
            orig_x1 = max(0, int((x1 - pad_w) / ratio))
            orig_y1 = max(0, int((y1 - pad_h) / ratio))
            orig_x2 = min(orig_w, int((x1 + w - pad_w) / ratio))
            orig_y2 = min(orig_h, int((y1 + h - pad_h) / ratio))

            box_w = max(1, orig_x2 - orig_x1)
            box_h = max(1, orig_y2 - orig_y1)

            boxes.append([orig_x1, orig_y1, box_w, box_h])
            confidences.append(score)
            class_ids.append(cls_id)

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            score_threshold=conf_threshold,
            nms_threshold=self.nms_threshold,
        )

        results = []
        if len(indices) > 0:
            # Flatten indices array across OpenCV versions
            flat_indices = indices.flatten() if hasattr(indices, "flatten") else [i[0] for i in indices]
            for idx in flat_indices:
                x, y, w, h = boxes[idx]
                results.append({
                    "class_id": class_ids[idx],
                    "confidence": float(confidences[idx]),
                    "bbox": [x, y, x + w, y + h],
                })

        return results

    def predict(
        self,
        frame: np.ndarray,
        conf_thresh: Optional[float] = None,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Perform full inference pipeline on a single frame."""
        if not self.is_loaded or self.session is None:
            return [], 0.0

        start_time = time.perf_counter()
        orig_shape = frame.shape[:2]  # [H, W]

        # 1. Preprocess
        blob, ratio, pad = self.preprocess(frame)

        # 2. Run Forward Pass with thread safety
        with self.lock:
            if self.backend_type == "onnxruntime":
                raw_outputs = self.session.run(self.output_names, {self.input_name: blob})
                net_output = raw_outputs[0]
            elif self.backend_type == "opencv_dnn":
                self.session.setInput(blob)
                net_output = self.session.forward(self.output_names[0])
            else:
                return [], 0.0

        # 3. Postprocess
        detections = self.postprocess(net_output, ratio, pad, orig_shape, conf_thresh)

        # 4. Latency measurement
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self.last_inference_time_ms = round(duration_ms, 2)
        self.total_inferences += 1
        
        # Exponential moving average for FPS / latency
        if self.avg_inference_time_ms == 0.0:
            self.avg_inference_time_ms = self.last_inference_time_ms
        else:
            self.avg_inference_time_ms = round(
                (self.avg_inference_time_ms * 0.9) + (self.last_inference_time_ms * 0.1), 2
            )

        return detections, self.last_inference_time_ms

    def get_status(self) -> Dict[str, Any]:
        """Return engine operational status and performance metrics."""
        return {
            "model_path": str(self.model_path.name),
            "is_loaded": self.is_loaded,
            "backend": self.backend_type,
            "input_resolution": list(self.input_size),
            "conf_threshold": self.conf_threshold,
            "nms_threshold": self.nms_threshold,
            "num_threads": self.num_threads,
            "last_latency_ms": self.last_inference_time_ms,
            "avg_latency_ms": self.avg_inference_time_ms,
            "estimated_fps": round(1000.0 / self.avg_inference_time_ms, 1) if self.avg_inference_time_ms > 0 else 0.0,
            "total_inferences": self.total_inferences,
        }

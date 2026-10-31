"""
FREY AI - High-Level Agricultural Plant Disease Detector
Wraps raw neural network detections with agronomic taxonomies, safety guidelines,
and visual bounding box annotations.

Guiding Principles:
1. Never interpret confidence as disease severity (confidence = model probability).
2. Do not declare a plant healthy just because no detection was produced.
3. Support multi-crop and multi-disease instances in a single camera frame.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

from frey.inference import InferenceEngine
from frey.taxonomy import parse_prediction, get_taxonomy_entry

logger = logging.getLogger("frey.detector")


class PlantDiseaseDetector:
    """High-level detection pipeline with agronomic validation and rendering."""

    def __init__(
        self,
        engine: InferenceEngine,
        default_conf: float = 0.25,
    ):
        self.engine = engine
        self.conf_threshold = default_conf

    def set_confidence_threshold(self, threshold: float):
        """Update live confidence threshold."""
        self.conf_threshold = max(0.05, min(0.99, float(threshold)))
        self.engine.conf_threshold = self.conf_threshold

    def detect(self, frame: np.ndarray) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run disease detection on frame and enrich with agricultural domain knowledge.
        
        Returns:
            detections: List of parsed detection dictionaries.
            metadata: Diagnostics including inference time, crop summary, and plant health assessment.
        """
        raw_detections, latency_ms = self.engine.predict(frame, conf_thresh=self.conf_threshold)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

        enriched_detections: List[Dict[str, Any]] = []
        healthy_count = 0
        diseased_count = 0
        crops_detected = set()

        for det in raw_detections:
            cls_id = det["class_id"]
            conf = det["confidence"]
            bbox = det["bbox"]

            parsed = parse_prediction(
                class_id=cls_id,
                confidence=conf,
                bbox=bbox,
                timestamp=timestamp,
            )

            if parsed["is_healthy"]:
                healthy_count += 1
            else:
                diseased_count += 1

            crops_detected.add(parsed["crop"])
            enriched_detections.append(parsed)

        # Agronomic plant status evaluation
        if len(enriched_detections) == 0:
            overall_status = "No Leaf Detected"
            status_color = "#94a3b8"  # slate gray
            recommendation = "No foliage detected in camera view. Ensure leaves are well-lit and centered within 30-50 cm."
        elif diseased_count > 0:
            overall_status = "Diseased Foliage Detected"
            status_color = "#ef4444"  # red
            recommendation = "Pathogenic symptoms identified. Inspect recommended management actions in Crop Analysis."
        else:
            overall_status = "Healthy Foliage Verified"
            status_color = "#22c55e"  # green
            recommendation = "All detected leaf canopies exhibit normal morphological characteristics."

        metadata = {
            "total_detections": len(enriched_detections),
            "healthy_count": healthy_count,
            "diseased_count": diseased_count,
            "crops_detected": sorted(list(crops_detected)),
            "overall_status": overall_status,
            "status_color": status_color,
            "general_recommendation": recommendation,
            "inference_time_ms": latency_ms,
            "timestamp": timestamp,
            "disclaimer": "Confidence represents neural network classification probability, NOT biological disease severity.",
        }

        return enriched_detections, metadata

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        show_labels: bool = True,
        show_conf: bool = True,
    ) -> np.ndarray:
        """Render high-contrast bounding boxes and label badges onto frame."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            is_healthy = det["is_healthy"]
            crop = det["crop"]
            disease = det["disease"]
            conf_pct = det["confidence_percent"]

            # Color coding: Green for healthy, Vibrant Red/Orange for disease
            if is_healthy:
                box_color = (46, 204, 113)    # Emerald Green (BGR)
                badge_bg = (24, 134, 75)
            else:
                box_color = (60, 76, 231)     # High-contrast Red/Coral (BGR)
                badge_bg = (30, 40, 160)

            # Draw outer bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2, cv2.LINE_AA)

            # Corner accents for modern edge-AI aesthetic
            corner_len = min(16, max(6, int((x2 - x1) * 0.15)))
            # Top-left
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), box_color, 3)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), box_color, 3)
            # Top-right
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), box_color, 3)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), box_color, 3)
            # Bottom-left
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), box_color, 3)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), box_color, 3)
            # Bottom-right
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), box_color, 3)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), box_color, 3)

            if not show_labels:
                continue

            # Text content
            label_text = f"{crop}: {disease}"
            if show_conf:
                label_text += f" ({conf_pct})"

            # Calculate badge dimensions
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.42
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

            badge_y1 = max(0, y1 - text_h - 8)
            badge_y2 = badge_y1 + text_h + 8
            badge_x1 = max(0, x1)
            badge_x2 = min(w, badge_x1 + text_w + 10)

            # Draw badge background
            cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), badge_bg, -1)
            cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), box_color, 1)

            # Draw label text
            text_pos = (badge_x1 + 5, badge_y2 - baseline - 2)
            cv2.putText(annotated, label_text, text_pos, font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        return annotated

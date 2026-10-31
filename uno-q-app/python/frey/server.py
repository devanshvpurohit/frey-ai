"""
FREY AI - Edge REST Backend & Dashboard Server
Powered by Flask, SQLite, OpenCV, and ONNX Runtime / OpenCV DNN.

Architecture:
- Asynchronous background camera thread decoupled from HTTP handlers.
- Rate-governed background inference worker preventing CPU starvation.
- Real-time MJPEG streaming with overlaid agricultural disease bounding boxes.
- Persistent SQLite detection log and system telemetry.
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, request, send_from_directory

from frey.camera import CameraCapture, discover_camera_devices
from frey.inference import InferenceEngine
from frey.detector import PlantDiseaseDetector
from frey.database import FreyDatabase
from frey.system_monitor import SystemMonitor
from frey.taxonomy import list_supported_crops, get_all_classes

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("frey.server")

# Base directory paths
DEPLOY_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = DEPLOY_DIR / "templates"
STATIC_DIR = DEPLOY_DIR / "static"
DATA_DIR = DEPLOY_DIR / "data"
MODELS_DIR = DEPLOY_DIR / "models"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Flask App
app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))

# Shared State Container
class FreyAppManager:
    def __init__(self):
        self.db = FreyDatabase(str(DATA_DIR / "frey.db"))
        self.monitor = SystemMonitor()
        
        # Load settings
        settings = self.db.get_all_settings()
        self.camera_device = settings.get("camera_device", "0")
        self.camera_res = settings.get("camera_res", "320x240")
        w, h = [int(x) for x in self.camera_res.split("x")]
        self.conf_threshold = float(settings.get("conf_threshold", "0.30"))
        self.inference_rate_hz = float(settings.get("inference_rate_hz", "3.0"))
        self.auto_save = settings.get("auto_save_history", "true").lower() == "true"
        self.overlay_boxes = settings.get("overlay_boxes", "true").lower() == "true"

        # Initialize Camera
        self.camera = CameraCapture(
            device_id=self.camera_device,
            width=w,
            height=h,
            fps=30,
            mock_if_missing=True,
        )

        # Initialize Inference Engine
        model_file = MODELS_DIR / "frey_yolo11n_416.onnx"
        self.engine = InferenceEngine(
            model_path=str(model_file),
            input_size=(416, 416),
            conf_threshold=self.conf_threshold,
            nms_threshold=float(settings.get("nms_threshold", "0.45")),
            num_threads=4,
        )

        self.detector = PlantDiseaseDetector(self.engine, default_conf=self.conf_threshold)

        # Threading and State
        self.latest_detections: List[Dict[str, Any]] = []
        self.latest_metadata: Dict[str, Any] = {}
        initial_frame = self.camera.latest_frame if self.camera.latest_frame is not None else np.zeros((h, w, 3), dtype=np.uint8)
        self.annotated_frame: np.ndarray = initial_frame.copy()
        _, initial_jpeg = cv2.imencode(".jpg", self.annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        self.annotated_jpeg: bytes = initial_jpeg.tobytes()
        self.frame_lock = threading.Lock()
        
        self.is_running = True
        self.last_detection_save_time = 0.0
        self.last_metrics_log_time = 0.0

        # Start workers
        self.camera.start()
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True, name="FreyInferenceWorker")
        self.inference_thread.start()

    def _inference_loop(self):
        """Continuous background inference pipeline decoupled from HTTP serving."""
        logger.info("Background inference pipeline active.")
        while self.is_running:
            loop_start = time.time()

            has_frame, frame, timestamp = self.camera.get_frame()
            if not has_frame or frame is None:
                time.sleep(0.05)
                continue

            # Run detection
            try:
                detections, metadata = self.detector.detect(frame)
                
                # Render annotated overlay if enabled
                if self.overlay_boxes:
                    annotated = self.detector.draw_detections(frame, detections)
                else:
                    annotated = frame.copy()

                # Compress to JPEG for smooth streaming
                _, jpeg_bytes = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])

                with self.frame_lock:
                    self.latest_detections = detections
                    self.latest_metadata = metadata
                    self.annotated_frame = annotated
                    self.annotated_jpeg = jpeg_bytes.tobytes()

                # Handle Auto-Save into SQLite
                now = time.time()
                if self.auto_save and len(detections) > 0 and (now - self.last_detection_save_time > 5.0):
                    # Save image snapshot
                    snap_name = f"det_{int(now)}.jpg"
                    snap_path = SNAPSHOTS_DIR / snap_name
                    cv2.imwrite(str(snap_path), annotated)
                    rel_path = f"/snapshots/{snap_name}"
                    self.db.log_batch_detections(detections, image_path=rel_path)
                    self.last_detection_save_time = now

                # Telemetry logging every 10 seconds
                if now - self.last_metrics_log_time > 10.0:
                    metrics = self.monitor.get_full_telemetry()
                    metrics["inference_fps"] = self.engine.get_status()["estimated_fps"]
                    metrics["inference_time_ms"] = metadata.get("inference_time_ms", 0.0)
                    self.db.log_system_metrics(metrics)
                    self.last_metrics_log_time = now

            except Exception as e:
                logger.error(f"Inference error in background worker: {e}")

            # Control inference frequency to avoid overloading embedded ARM CPU
            elapsed = time.time() - loop_start
            target_period = 1.0 / max(0.5, self.inference_rate_hz)
            sleep_time = max(0.01, target_period - elapsed)
            time.sleep(sleep_time)

    def stop(self):
        """Clean shutdown of all subsystems."""
        self.is_running = False
        self.camera.stop()
        logger.info("Manager shutdown complete.")


# Instantiate application manager
manager: Optional[FreyAppManager] = None

def get_manager() -> FreyAppManager:
    global manager
    if manager is None:
        manager = FreyAppManager()
    return manager


# ==========================================
#              FLASK ROUTES
# ==========================================

@app.route("/")
def index():
    """Render main FREY AI dashboard."""
    mgr = get_manager()
    settings = mgr.db.get_all_settings()
    crops = list_supported_crops()
    return render_template("index.html", settings=settings, crops=crops)


@app.route("/api/status", methods=["GET"])
def get_status():
    """Consolidated operational health status."""
    mgr = get_manager()
    cam_status = mgr.camera.get_status()
    engine_status = mgr.engine.get_status()
    telemetry = mgr.monitor.get_full_telemetry()
    stats = mgr.db.get_summary_stats()

    with mgr.frame_lock:
        meta = mgr.latest_metadata
        total_live = len(mgr.latest_detections)

    return jsonify({
        "status": "healthy" if engine_status["is_loaded"] and cam_status["connected"] else "degraded",
        "camera": cam_status,
        "model": engine_status,
        "system": telemetry,
        "stats": stats,
        "live": {
            "total_detections": total_live,
            "overall_status": meta.get("overall_status", "Initializing..."),
            "status_color": meta.get("status_color", "#94a3b8"),
            "general_recommendation": meta.get("general_recommendation", ""),
            "inference_time_ms": meta.get("inference_time_ms", 0.0),
        }
    })


@app.route("/api/detections", methods=["GET"])
def get_live_detections():
    """Return all detections from latest frame with agronomic classification."""
    mgr = get_manager()
    with mgr.frame_lock:
        return jsonify({
            "detections": mgr.latest_detections,
            "metadata": mgr.latest_metadata,
        })


@app.route("/api/history", methods=["GET"])
def get_history():
    """Query detection history with filtering, searching, and pagination."""
    mgr = get_manager()
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    crop = request.args.get("crop", None)
    search = request.args.get("search", None)
    
    is_healthy = None
    if "is_healthy" in request.args:
        val = request.args.get("is_healthy").lower()
        if val in ["true", "1"]:
            is_healthy = True
        elif val in ["false", "0"]:
            is_healthy = False

    records, total = mgr.db.get_history(
        limit=limit,
        offset=offset,
        crop=crop,
        is_healthy=is_healthy,
        search=search,
    )

    return jsonify({
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Fetch current settings and available hardware devices."""
    mgr = get_manager()
    settings = mgr.db.get_all_settings()
    devices = discover_camera_devices()
    return jsonify({
        "settings": settings,
        "available_devices": devices,
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update runtime configuration parameters."""
    mgr = get_manager()
    data = request.get_json(force=True) if request.is_json else request.form.to_dict()

    if "conf_threshold" in data:
        conf = float(data["conf_threshold"])
        mgr.detector.set_confidence_threshold(conf)
        mgr.db.set_setting("conf_threshold", conf)

    if "inference_rate_hz" in data:
        hz = float(data["inference_rate_hz"])
        mgr.inference_rate_hz = max(0.5, min(10.0, hz))
        mgr.db.set_setting("inference_rate_hz", mgr.inference_rate_hz)

    if "auto_save_history" in data:
        val = str(data["auto_save_history"]).lower() in ["true", "1"]
        mgr.auto_save = val
        mgr.db.set_setting("auto_save_history", "true" if val else "false")

    if "overlay_boxes" in data:
        val = str(data["overlay_boxes"]).lower() in ["true", "1"]
        mgr.overlay_boxes = val
        mgr.db.set_setting("overlay_boxes", "true" if val else "false")

    if "camera_device" in data:
        dev = str(data["camera_device"])
        if dev != mgr.camera_device:
            mgr.camera_device = dev
            mgr.db.set_setting("camera_device", dev)
            # Restart camera with new device
            mgr.camera.stop()
            w, h = [int(x) for x in mgr.camera_res.split("x")]
            mgr.camera = CameraCapture(device_id=dev, width=w, height=h, fps=30, mock_if_missing=True)
            mgr.camera.start()

    if "camera_res" in data:
        res = str(data["camera_res"])
        if res != mgr.camera_res:
            mgr.camera_res = res
            mgr.db.set_setting("camera_res", res)
            w, h = [int(x) for x in res.split("x")]
            mgr.camera.width = w
            mgr.camera.height = h

    return jsonify({"success": True, "settings": mgr.db.get_all_settings()})


@app.route("/api/camera/start", methods=["POST"])
def start_camera():
    """Start or restart the camera acquisition pipeline."""
    mgr = get_manager()
    if not mgr.camera.is_running:
        mgr.camera.start()
    return jsonify({"success": True, "status": mgr.camera.get_status()})


@app.route("/api/camera/stop", methods=["POST"])
def stop_camera():
    """Stop camera acquisition pipeline."""
    mgr = get_manager()
    mgr.camera.stop()
    return jsonify({"success": True, "status": mgr.camera.get_status()})


@app.route("/api/snapshot", methods=["POST", "GET"])
def take_snapshot():
    """Manually trigger and save current frame snapshot with detection metadata."""
    mgr = get_manager()
    with mgr.frame_lock:
        if mgr.annotated_frame is None:
            return jsonify({"success": False, "error": "No frame available"}), 400
        frame_copy = mgr.annotated_frame.copy()
        detections_copy = list(mgr.latest_detections)

    now = int(time.time())
    snap_name = f"manual_snap_{now}.jpg"
    snap_path = SNAPSHOTS_DIR / snap_name
    cv2.imwrite(str(snap_path), frame_copy)
    rel_path = f"/snapshots/{snap_name}"

    record_ids = []
    if detections_copy:
        for det in detections_copy:
            rec_id = mgr.db.log_detection(det, image_path=rel_path)
            record_ids.append(rec_id)
    else:
        # Save snapshot even with no detection
        rec_id = mgr.db.log_detection({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "crop": "Unidentified",
            "disease": "No Foliage Detected",
            "is_healthy": False,
            "confidence": 0.0,
            "bbox": [],
            "recommendation": "Manual snapshot saved.",
        }, image_path=rel_path)
        record_ids.append(rec_id)

    return jsonify({
        "success": True,
        "image_path": rel_path,
        "record_ids": record_ids,
        "detections_count": len(detections_copy),
    })


@app.route("/api/crops", methods=["GET"])
def get_crops():
    """Return taxonomy of supported crops and conditions."""
    return jsonify({
        "crops": list_supported_crops(),
        "classes": get_all_classes(),
    })


@app.route("/snapshots/<filename>")
def serve_snapshot(filename):
    """Serve saved detection snapshot images."""
    return send_from_directory(str(SNAPSHOTS_DIR), filename)


def generate_mjpeg_stream():
    """MJPEG streaming generator with low memory buffer allocation."""
    mgr = get_manager()
    while True:
        with mgr.frame_lock:
            jpeg = mgr.annotated_jpeg

        if jpeg is None:
            time.sleep(0.04)
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
        time.sleep(0.033)  # ~30 FPS max stream rate


@app.route("/video_feed")
@app.route("/api/stream")
def video_feed():
    """Multipart live MJPEG video stream endpoint."""
    return Response(
        generate_mjpeg_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def create_app():
    """Application factory for WSGI / Gunicorn / systemd deployment."""
    get_manager()
    return app


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FREY AI Dashboard Backend")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Listen address")
    parser.add_argument("--port", type=int, default=5000, help="Listen port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Pre-initialize manager
    get_manager()
    logger.info(f"Starting FREY AI Server on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

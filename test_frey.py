#!/usr/bin/env python3
"""
FREY AI - Comprehensive Edge Verification Test Suite
Verifies:
1. Taxonomy resolution & agronomic rules
2. ONNX model loading & tensor dimensions
3. Forward pass & NMS post-processing
4. Visual annotation & bounding boxes
5. SQLite persistence & history queries
6. Hardware system telemetry
7. Camera grabber & synthetic fallback
8. Flask REST API endpoints & live stream
"""

import os
import sys
import time
import json
import unittest
from pathlib import Path
import numpy as np
import cv2

# Add deployment to PYTHONPATH
DEPLOY_DIR = Path(__file__).resolve().parent / "deployment"
sys.path.insert(0, str(DEPLOY_DIR))

from frey.taxonomy import (
    PLANTDOC_CLASSES,
    get_taxonomy_entry,
    parse_prediction,
    list_supported_crops,
)
from frey.inference import InferenceEngine
from frey.detector import PlantDiseaseDetector
from frey.database import FreyDatabase
from frey.system_monitor import SystemMonitor
from frey.camera import CameraCapture, discover_camera_devices
from frey.server import app, get_manager


class TestFreyAI(unittest.TestCase):

    def test_01_taxonomy(self):
        """Test canonical taxonomy and agronomic safety principles."""
        print("\n[TEST 1] Verifying Taxonomy & Agronomic Safety...")
        # Check class count
        self.assertEqual(len(PLANTDOC_CLASSES), 29)

        # Check lookup by ID
        entry_0 = get_taxonomy_entry(0)
        self.assertIsNotNone(entry_0)
        self.assertEqual(entry_0["crop"], "Apple")
        self.assertFalse(entry_0["is_healthy"])

        entry_1 = get_taxonomy_entry(1)
        self.assertTrue(entry_1["is_healthy"])

        # Check lookup by name
        tomato_early = get_taxonomy_entry("Tomato Early blight leaf")
        self.assertIsNotNone(tomato_early)
        self.assertEqual(tomato_early["disease"], "Early Blight")

        # Test prediction parsing
        pred = parse_prediction(class_id=20, confidence=0.88, bbox=[50, 60, 200, 220])
        self.assertEqual(pred["crop"], "Tomato")
        self.assertEqual(pred["disease"], "Early Blight")
        self.assertIn("Confidence reflects classification probability", pred["severity_disclaimer"])

        crops = list_supported_crops()
        self.assertIn("Tomato", crops)
        self.assertIn("Potato", crops)
        self.assertIn("Rice", crops)
        print("  -> Taxonomy verification PASSED.")

    def test_02_inference_engine(self):
        """Test ONNX model loading and forward pass."""
        print("\n[TEST 2] Verifying ONNX Inference Engine...")
        model_path = DEPLOY_DIR / "models" / "frey_yolo11n_416.onnx"
        self.assertTrue(model_path.exists(), f"Model missing: {model_path}")

        engine = InferenceEngine(
            model_path=str(model_path),
            input_size=(416, 416),
            conf_threshold=0.20,
            nms_threshold=0.45,
            num_threads=4,
        )
        self.assertTrue(engine.is_loaded)
        self.assertIn(engine.backend_type, ["onnxruntime", "opencv_dnn"])

        # Create dummy image
        test_img = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(test_img, (160, 120), 50, (34, 139, 34), -1)

        detections, latency_ms = engine.predict(test_img)
        self.assertIsInstance(detections, list)
        self.assertGreater(latency_ms, 0.0)
        print(f"  -> Model loaded via {engine.backend_type}. Inference latency: {latency_ms:.2f} ms. PASSED.")

    def test_03_detector_and_annotation(self):
        """Test PlantDiseaseDetector and bounding box drawing."""
        print("\n[TEST 3] Verifying Agricultural Detector & Annotation...")
        model_path = DEPLOY_DIR / "models" / "frey_yolo11n_416.onnx"
        engine = InferenceEngine(str(model_path), input_size=(416, 416))
        detector = PlantDiseaseDetector(engine, default_conf=0.25)

        test_img = np.zeros((240, 320, 3), dtype=np.uint8)
        detections, meta = detector.detect(test_img)

        self.assertIn("overall_status", meta)
        self.assertIn("disclaimer", meta)

        # Test annotator with mock detection
        mock_det = [{
            "class_id": 20,
            "crop": "Tomato",
            "disease": "Early Blight",
            "is_healthy": False,
            "confidence": 0.85,
            "confidence_percent": "85.0%",
            "bbox": [40, 40, 150, 150],
        }]
        annotated = detector.draw_detections(test_img, mock_det)
        self.assertEqual(annotated.shape, test_img.shape)
        print("  -> Detector & Annotation PASSED.")

    def test_04_database_operations(self):
        """Test SQLite telemetry and history storage."""
        print("\n[TEST 4] Verifying SQLite Database Operations...")
        test_db_path = DEPLOY_DIR / "data" / "test_frey.db"
        if test_db_path.exists():
            test_db_path.unlink()

        db = FreyDatabase(str(test_db_path))

        # Log single detection
        rec_id = db.log_detection({
            "timestamp": "2026-10-31T12:00:00",
            "crop": "Potato",
            "disease": "Late Blight",
            "is_healthy": False,
            "confidence": 0.92,
            "bbox": [10, 20, 100, 120],
            "recommendation": "Apply metalaxyl immediately.",
        })
        self.assertGreater(rec_id, 0)

        # Query history
        history, total = db.get_history(limit=10)
        self.assertEqual(total, 1)
        self.assertEqual(history[0]["crop"], "Potato")
        self.assertFalse(history[0]["is_healthy"])

        # Test settings
        db.set_setting("conf_threshold", "0.40")
        val = db.get_setting("conf_threshold")
        self.assertEqual(val, "0.40")

        # Clean test DB
        if test_db_path.exists():
            test_db_path.unlink()
        print("  -> SQLite Database PASSED.")

    def test_05_system_monitor(self):
        """Test hardware telemetry monitor."""
        print("\n[TEST 5] Verifying System Hardware Monitor...")
        mon = SystemMonitor()
        telemetry = mon.get_full_telemetry()
        self.assertIn("cpu_percent", telemetry)
        self.assertIn("ram_percent", telemetry)
        self.assertIn("ram_total_mb", telemetry)
        print(f"  -> Host CPU: {telemetry['cpu_percent']}%, RAM: {telemetry['ram_percent']}%. PASSED.")

    def test_06_camera_system(self):
        """Test camera discovery and synthetic fallback."""
        print("\n[TEST 6] Verifying Camera Capture System...")
        devices = discover_camera_devices()
        self.assertIsInstance(devices, list)

        cam = CameraCapture(device_id=0, width=320, height=240, fps=15, mock_if_missing=True)
        cam.start()
        time.sleep(0.5)

        ret, frame, ts = cam.get_frame()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[:2], (240, 320))

        status = cam.get_status()
        self.assertTrue(status["connected"])
        cam.stop()
        print(f"  -> Camera Capture PASSED (mock_mode={status['mock_mode']}).")

    def test_07_flask_rest_api(self):
        """Test Flask REST endpoints."""
        print("\n[TEST 7] Verifying Flask REST API...")
        client = app.test_client()

        # GET /api/status
        res_status = client.get("/api/status")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.get_json()
        self.assertIn("camera", data_status)
        self.assertIn("model", data_status)
        self.assertIn("system", data_status)

        # GET /api/detections
        res_det = client.get("/api/detections")
        self.assertEqual(res_det.status_code, 200)

        # GET /api/settings
        res_sett = client.get("/api/settings")
        self.assertEqual(res_sett.status_code, 200)

        # POST /api/settings
        res_upd = client.post("/api/settings", json={"conf_threshold": 0.35})
        self.assertEqual(res_upd.status_code, 200)

        # GET /api/crops
        res_crops = client.get("/api/crops")
        self.assertEqual(res_crops.status_code, 200)

        # GET /api/history
        res_hist = client.get("/api/history")
        self.assertEqual(res_hist.status_code, 200)

        # POST /api/snapshot
        res_snap = client.post("/api/snapshot")
        self.assertEqual(res_snap.status_code, 200)

        print("  -> All REST Endpoints PASSED.")


if __name__ == "__main__":
    unittest.main()

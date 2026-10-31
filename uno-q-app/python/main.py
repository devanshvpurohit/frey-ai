#!/usr/bin/env python3
"""
FREY AI — Arduino App Lab MPU Application Entrypoint
=====================================================
Runs on the onboard Linux processor (Qualcomm QRB2210) of the Arduino UNO Q.

Features:
- Starts the FREY AI camera acquisition pipeline, YOLO11n ONNX inference engine,
  SQLite database, and Flask REST dashboard on port 5000.
- Connects to the Arduino App Lab Bridge (arduino.app_utils.Bridge) to exchange
  real-time agricultural telemetry with the STM32/Zephyr microcontroller sketch.
- Enables physical hardware triggers:
    * Microcontroller button presses can invoke 'triggerSnapshot' over Bridge.
    * Microcontroller can query current disease status via 'getDiseaseStatus'.
    * Python engine notifies microcontroller via Bridge.notify("onDiseaseAlert")
      when foliar lesions are detected, triggering physical alert LEDs / relays.
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path

# Add python directory to sys.path
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

# Import Arduino App Lab SDK (with graceful fallback for off-board testing)
try:
    from arduino.app_utils import App, Bridge
    HAS_APP_LAB = True
except ImportError:
    HAS_APP_LAB = False

    class MockBridge:
        def provide(self, name, func):
            logging.info(f"[MockBridge] Registered provider for '{name}'")
        def notify(self, name, payload):
            logging.info(f"[MockBridge] Notification '{name}': {payload}")

    class MockApp:
        def run(self, user_loop=None):
            logging.info("[MockApp] Running user loop. Press Ctrl+C to stop.")
            try:
                while True:
                    if user_loop:
                        user_loop()
                    else:
                        time.sleep(1)
            except KeyboardInterrupt:
                logging.info("[MockApp] Stopped.")

    Bridge = MockBridge()
    App = MockApp()

# Import FREY AI server and manager
from frey.server import app, get_manager

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("frey.unoq_app")


class UnoQBridgeController:
    """Coordinates Python AI inference with the Arduino MCU sketch."""

    def __init__(self, manager):
        self.mgr = manager
        self.last_alert_state = None
        self._register_bridge_methods()

    def _register_bridge_methods(self):
        """Expose functions that the microcontroller sketch can invoke."""
        
        def getDiseaseStatus(params=None):
            """Invoked by MCU sketch to check if current canopy is healthy/diseased."""
            with self.mgr.frame_lock:
                meta = self.mgr.latest_metadata
                total_live = len(self.mgr.latest_detections)
                diseased = meta.get("diseased_count", 0)
                healthy = meta.get("healthy_count", 0)
                primary_crop = "None"
                primary_condition = "None"
                if total_live > 0:
                    primary_crop = self.mgr.latest_detections[0].get("crop", "Unknown")
                    primary_condition = self.mgr.latest_detections[0].get("disease", "Unknown")

            return json.dumps({
                "status": "DISEASED" if diseased > 0 else ("HEALTHY" if healthy > 0 else "NO_CANOPY"),
                "diseased_count": diseased,
                "healthy_count": healthy,
                "crop": primary_crop,
                "condition": primary_condition,
            })

        def triggerSnapshot(params=None):
            """Invoked when a physical push button is pressed on the Arduino board."""
            logger.info("[Bridge] Hardware snapshot trigger received from Arduino MCU!")
            with self.mgr.frame_lock:
                if self.mgr.annotated_frame is None:
                    return json.dumps({"success": False, "error": "No frame available"})
                frame_copy = self.mgr.annotated_frame.copy()
                dets_copy = list(self.mgr.latest_detections)

            now = int(time.time())
            snap_path = APP_DIR / "data" / "snapshots" / f"hw_snap_{now}.jpg"
            snap_path.parent.mkdir(parents=True, exist_ok=True)
            import cv2
            cv2.imwrite(str(snap_path), frame_copy)

            if dets_copy:
                for d in dets_copy:
                    self.mgr.db.log_detection(d, image_path=f"/snapshots/hw_snap_{now}.jpg")

            return json.dumps({"success": True, "path": str(snap_path)})

        # Register providers
        Bridge.provide("getDiseaseStatus", getDiseaseStatus)
        Bridge.provide("triggerSnapshot", triggerSnapshot)
        logger.info("[Bridge] Registered 'getDiseaseStatus' and 'triggerSnapshot' RPC endpoints.")

    def poll_and_notify_mcu(self):
        """Check latest detection state and send updates to the MCU sketch."""
        with self.mgr.frame_lock:
            meta = self.mgr.latest_metadata
            total_live = len(self.mgr.latest_detections)
            diseased = meta.get("diseased_count", 0)
            healthy = meta.get("healthy_count", 0)

        # 0 = No leaf, 1 = Healthy leaf, 2 = Diseased leaf
        current_state = 2 if diseased > 0 else (1 if healthy > 0 else 0)

        if current_state != self.last_alert_state:
            self.last_alert_state = current_state
            payload = json.dumps({
                "state": current_state,
                "label": "DISEASED" if current_state == 2 else ("HEALTHY" if current_state == 1 else "NO_CANOPY"),
                "timestamp": int(time.time()),
            })
            try:
                Bridge.notify("onDiseaseAlert", payload)
                logger.info(f"[Bridge] Dispatched MCU notification 'onDiseaseAlert': {payload}")
            except Exception as e:
                logger.debug(f"[Bridge] Notification error: {e}")


def run_flask_server(host="0.0.0.0", port=5000):
    """Run Flask HTTP server in daemon thread."""
    logger.info(f"Starting FREY AI Dashboard on http://{host}:{port}")
    # Disable Flask's default banner for clean App Lab logs
    cli = sys.modules.get('flask.cli')
    if cli:
        cli.show_server_banner = lambda *x: None
    app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)


def main():
    print("=" * 65)
    print("      FREY AI — ARDUINO UNO Q APP LAB RUNTIME")
    print("=" * 65)
    print("Target Architecture : Qualcomm QRB2210 Linux Processor (MPU)")
    print("Co-Processor        : STM32 Real-Time Microcontroller (MCU)")
    print("Inference Engine    : Ultralytics YOLO11n ONNX (416x416)")
    print("Dashboard Port      : http://0.0.0.0:5000")
    print("=" * 65)

    # Initialize shared manager (starts camera and inference workers)
    mgr = get_manager()
    bridge_ctrl = UnoQBridgeController(mgr)

    # Start Flask Web Dashboard in background thread
    flask_thread = threading.Thread(
        target=run_flask_server,
        kwargs={"host": "0.0.0.0", "port": 5000},
        daemon=True,
        name="FreyFlaskServer"
    )
    flask_thread.start()

    # User loop for App Lab
    def app_loop():
        bridge_ctrl.poll_and_notify_mcu()
        time.sleep(1.0)

    # Execute App Lab lifecycle
    App.run(user_loop=app_loop)


if __name__ == "__main__":
    main()

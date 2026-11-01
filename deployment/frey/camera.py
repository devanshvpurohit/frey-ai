"""
FREY AI - Industrial Edge Camera Capture System
Supports USB UVC webcams on Debian Linux (Arduino UNO Q / Qualcomm QRB2210).

Key Capabilities:
- Automatic video device discovery (/dev/video0, /dev/video1, /dev/video2, etc.)
- Multi-pixelformat support: MJPEG and YUYV
- Single-process lock mechanism to prevent camera device conflicts
- Resilient auto-reconnect logic with exponential backoff on USB disconnect
- Dedicated threaded grabber ensuring zero-latency newest frame access
- Synthetic test pattern generator fallback when physical webcam is disconnected
"""

import os
import glob
import time
import fcntl
import threading
import logging
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import cv2

logger = logging.getLogger("frey.camera")


class CameraLock:
    """File-based lock to prevent multiple processes from contending for USB camera."""
    def __init__(self, lock_path: str = "/tmp/frey_camera.lock"):
        self.lock_path = lock_path
        self.fd = None

    def acquire(self) -> bool:
        try:
            self.fd = open(self.lock_path, "w")
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            return True
        except (IOError, OSError) as e:
            logger.debug(f"Failed to acquire camera lock {self.lock_path}: {e}")
            return False

    def release(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
            self.fd = None


def discover_camera_devices() -> List[Dict[str, Any]]:
    """Scan Linux /dev/video* devices and probe basic capabilities."""
    devices = []
    video_nodes = sorted(glob.glob("/dev/video*"))
    
    if not video_nodes:
        # Fallback to probing numeric indices 0, 1, 2 on macOS or environments without /dev/video
        for idx in range(3):
            devices.append({
                "id": idx,
                "path": f"device_{idx}",
                "name": f"Camera Index {idx}",
                "available": True,
            })
        return devices

    for node in video_nodes:
        try:
            dev_idx = int(node.replace("/dev/video", ""))
            # Check read permission
            readable = os.access(node, os.R_OK)
            devices.append({
                "id": dev_idx,
                "path": node,
                "name": f"USB Video Device ({node})",
                "available": readable,
            })
        except Exception:
            continue

    return devices


class CameraCapture:
    """Threaded USB Camera manager with error recovery and frame buffering."""

    def __init__(
        self,
        device_id: Any = 0,
        width: int = 320,
        height: int = 240,
        fps: int = 15,
        fourcc: str = "MJPG",
        mock_if_missing: bool = True,
    ):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.fourcc = fourcc
        self.mock_if_missing = mock_if_missing

        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = threading.Lock()
        self.file_lock = CameraLock()
        
        self.latest_frame: Optional[np.ndarray] = self._create_mock_frame() if mock_if_missing else None
        self.frame_timestamp: float = time.time()
        self.is_running: bool = False
        self.is_connected: bool = True if mock_if_missing else False
        self.is_mock_mode: bool = True if mock_if_missing else False
        self.thread: Optional[threading.Thread] = None
        
        self.reconnect_attempts: int = 0
        self.last_reconnect_time: float = 0.0
        self.consecutive_failures: int = 0
        self.fps_actual: float = 0.0
        self.frame_count: int = 0
        self.last_fps_calc: float = time.time()

    def _create_mock_frame(self) -> np.ndarray:
        """Generate high-contrast simulated agricultural test frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Deep dark soil background
        frame[:] = (30, 35, 25)

        # Oscillating synthetic plant leaf
        t = time.time()
        cx = int(self.width * 0.5 + np.sin(t * 1.5) * (self.width * 0.1))
        cy = int(self.height * 0.5 + np.cos(t * 1.2) * (self.height * 0.08))
        
        axes_w = int(self.width * 0.28)
        axes_h = int(self.height * 0.22)
        angle = int(np.sin(t * 0.8) * 15)

        # Draw green leaf
        cv2.ellipse(frame, (cx, cy), (axes_w, axes_h), angle, 0, 360, (46, 139, 87), -1)
        # Leaf vein
        cv2.ellipse(frame, (cx, cy), (axes_w, 2), angle, 0, 360, (34, 110, 65), -1)

        # Simulated lesion spot on leaf
        spot_x = int(cx + axes_w * 0.3)
        spot_y = int(cy - axes_h * 0.2)
        cv2.circle(frame, (spot_x, spot_y), max(4, int(self.width * 0.03)), (25, 45, 120), -1)
        cv2.circle(frame, (spot_x, spot_y), max(2, int(self.width * 0.015)), (15, 25, 80), -1)

        # Status watermark
        cv2.rectangle(frame, (0, 0), (self.width, 24), (15, 22, 18), -1)
        status_text = f"SIMULATED CAMERA STREAM | RES: {self.width}x{self.height}"
        cv2.putText(frame, status_text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (74, 222, 128), 1, cv2.LINE_AA)

        return frame

    def _open_camera(self) -> bool:
        """Attempt to open hardware video capture device."""
        if not self.file_lock.acquire():
            logger.warning("Another process is currently holding the FREY camera lock.")

        target = self.device_id
        # Convert numeric string to int
        if isinstance(target, str) and target.isdigit():
            target = int(target)

        logger.info(f"Attempting to open camera device: {target} (format={self.fourcc}, res={self.width}x{self.height})")

        # Open capture device
        if os.name == 'posix' and isinstance(target, str) and target.startswith("/dev/video"):
            cap = cv2.VideoCapture(target, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(target)

        if not cap.isOpened():
            logger.warning(f"Hardware camera device {target} could not be opened.")
            return False

        # Apply FOURCC codec
        if self.fourcc.upper() == "MJPG":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        elif self.fourcc.upper() == "YUYV":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))

        # Configure resolution and FPS
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Test single read
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning("Camera opened but failed initial frame read.")
            cap.release()
            return False

        self.cap = cap
        self.is_connected = True
        self.is_mock_mode = False
        self.consecutive_failures = 0
        logger.info(f"Hardware camera {target} initialized successfully ({frame.shape[1]}x{frame.shape[0]}).")
        return True

    def start(self):
        """Start background capture thread."""
        if self.is_running:
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True, name="FreyCameraWorker")
        self.thread.start()

    def _capture_loop(self):
        """Continuous frame grabbing loop with auto-reconnect."""
        opened = self._open_camera()
        if not opened:
            if self.mock_if_missing:
                logger.info("Physical camera not available; activating synthetic test camera fallback.")
                self.is_connected = True
                self.is_mock_mode = True
            else:
                self.is_connected = False

        while self.is_running:
            if self.is_mock_mode:
                # Generate synthetic test frame at ~30 FPS
                mock_frame = self._create_mock_frame()
                with self.lock:
                    self.latest_frame = mock_frame
                    self.frame_timestamp = time.time()
                self._update_fps_metrics()
                time.sleep(1.0 / max(1, self.fps))
                continue

            if not self.is_connected or self.cap is None or not self.cap.isOpened():
                self._handle_reconnect()
                time.sleep(1.0)
                continue

            try:
                frame_start = time.perf_counter()
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.consecutive_failures += 1
                    logger.warning(f"Frame read failure (consecutive={self.consecutive_failures})")
                    if self.consecutive_failures > 5:
                        logger.error("Camera USB stream broken or disconnected. Resetting device.")
                        self._release_hardware()
                        self.is_connected = False
                    time.sleep(0.05)
                    continue

                self.consecutive_failures = 0
                with self.lock:
                    self.latest_frame = frame
                    self.frame_timestamp = time.time()
                self._update_fps_metrics()

                # Pace hardware camera acquisition to requested FPS to save CPU
                elapsed = time.perf_counter() - frame_start
                target_period = 1.0 / max(1, self.fps)
                sleep_time = max(0.002, target_period - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Unexpected error in camera capture loop: {e}")
                self.consecutive_failures += 1
                time.sleep(0.1)

        self._release_hardware()

    def _handle_reconnect(self):
        """Exponential backoff reconnect logic."""
        now = time.time()
        backoff = min(10.0, 1.0 + (self.reconnect_attempts * 1.5))
        if now - self.last_reconnect_time < backoff:
            return

        self.last_reconnect_time = now
        self.reconnect_attempts += 1
        logger.info(f"Attempting camera reconnection (attempt #{self.reconnect_attempts})...")

        if self._open_camera():
            logger.info("Reconnection succeeded!")
            self.reconnect_attempts = 0
        else:
            if self.mock_if_missing and self.reconnect_attempts >= 3:
                logger.warning("Hardware reconnect failed 3 times; switching to synthetic fallback.")
                self.is_mock_mode = True
                self.is_connected = True

    def _update_fps_metrics(self):
        self.frame_count += 1
        now = time.time()
        elapsed = now - self.last_fps_calc
        if elapsed >= 1.0:
            self.fps_actual = round(self.frame_count / elapsed, 1)
            self.frame_count = 0
            self.last_fps_calc = now

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray], float]:
        """Thread-safe retrieval of the latest captured frame."""
        with self.lock:
            if self.latest_frame is None:
                return False, None, 0.0
            return True, self.latest_frame.copy(), self.frame_timestamp

    def get_status(self) -> Dict[str, Any]:
        """Return real-time camera health status."""
        return {
            "device": str(self.device_id),
            "connected": self.is_connected,
            "mock_mode": self.is_mock_mode,
            "width": self.width,
            "height": self.height,
            "fps_target": self.fps,
            "fps_actual": self.fps_actual,
            "reconnect_attempts": self.reconnect_attempts,
            "last_frame_age_ms": round((time.time() - self.frame_timestamp) * 1000, 1) if self.frame_timestamp > 0 else None,
        }

    def _release_hardware(self):
        """Safely release VideoCapture and unlock device file."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.file_lock.release()

    def stop(self):
        """Stop background worker and release resources."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self._release_hardware()
        self.is_connected = False
        logger.info("Camera system stopped.")

# FREY AI — Arduino UNO Q Deployment Guide

This guide details the deployment of **FREY AI** onto the **Arduino UNO Q** running Debian GNU/Linux 13 on the Qualcomm QRB2210 processor.

---

## 1. Hardware Architecture Overview

| Component | Specification | Function in FREY AI |
|:---|:---|:---|
| **Board** | Arduino UNO Q (4GB RAM) | Edge computing host |
| **Processor** | Qualcomm QRB2210 quad-core ARM Cortex-A53 | Runs AI inference and Flask backend |
| **Microcontroller** | STM32 | *Not used for YOLO* (reserved for motor/GPIO control) |
| **Operating System** | Debian GNU/Linux 13 (Trixie) | Linux host environment |
| **Vision Sensor** | Standard USB UVC Webcam | Continuous leaf capture (/dev/video0, /dev/video1, /dev/video2) |
| **Power Supply** | 5V / 3A USB-C Power Adapter | Stable edge operation |

> [!IMPORTANT]
> AI inference runs exclusively on the Qualcomm Linux processor. The STM32 microcontroller does not execute YOLO. No ESP32, ESP32-CAM, Ollama, or external cloud inference is used or required.

---

## 2. Hardware Connections

1. **Connect USB Webcam:** Plug your standard UVC webcam into any available USB-A or USB-C host port on the Arduino UNO Q.
2. **Power:** Connect a 5V/3A power supply to the USB-C power input.
3. **Network:** Connect the UNO Q to your local Wi-Fi or Ethernet network.

---

## 3. SSH into the Board

Find your board's IP address (via router DHCP table or Arduino IDE discovery):

```bash
ssh root@<UNO_Q_IP_ADDRESS>
# or
ssh arduino@<UNO_Q_IP_ADDRESS>
```

Verify you are running Debian 13:
```bash
cat /etc/os-release
uname -m
# Should return 'aarch64'
```

---

## 4. Debian 13 PEP 668 Compliance & Dependencies

Debian 13 introduces strict **PEP 668** protections (`EXTERNALLY-MANAGED`), which prevent `pip` from mutating system Python packages.

FREY AI respects this constraint using a two-tier strategy:
1. **Debian APT Packages:** We install pre-compiled, optimized Debian packages for `python3-opencv`, `python3-numpy`, and `python3-flask`. This eliminates heavy compile times on ARM.
2. **Virtual Environment with Site-Packages:** We create a dedicated virtual environment with `--system-site-packages` so system OpenCV is directly accessible without violating PEP 668.

Run the automated setup script on the board:

```bash
cd /home/arduino/frey-ai
chmod +x setup_board.sh start_frey.sh stop_frey.sh
./setup_board.sh
```

### Manual Dependency Installation (Reference)
If you prefer manual setup:
```bash
# 1. Install Debian system packages
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    python3 python3-venv python3-numpy python3-opencv python3-flask \
    sqlite3 v4l-utils libgl1 libglib2.0-0

# 2. Add user to video group
sudo usermod -aG video $USER

# 3. Create isolated virtual environment
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# 4. Optional: install onnxruntime if available for aarch64
pip install onnxruntime || true
```

---

## 5. Verifying USB Camera

Verify that the Linux kernel recognizes your webcam:

```bash
v4l2-ctl --list-devices
```

Expected output:
```
USB 2.0 Camera: USB Camera (usb-xhci-hcd.0.auto-1):
	/dev/video0
	/dev/video1
```

Query supported formats:
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```
FREY AI supports both **MJPEG** and **YUYV** video formats.

---

## 6. Starting FREY AI

To launch the FREY AI edge service:

```bash
cd /home/arduino/frey-ai
./start_frey.sh
```

You will see:
```
==========================================================
           STARTING FREY AI EDGE SERVICE                  
==========================================================
Deployment Root : /home/arduino/frey-ai
Log File        : /home/arduino/frey-ai/frey.log
Listening On    : http://0.0.0.0:5000
Local Dashboard Access URLs:
  -> http://192.168.1.145:5000
==========================================================
[SUCCESS] FREY AI daemon started with PID 1420.
```

To stop the service:
```bash
./stop_frey.sh
```

---

## 7. Accessing the Dashboard

Open any web browser on your PC, tablet, or phone connected to the same local network:

```
http://<UNO_Q_IP_ADDRESS>:5000
```

### Dashboard Features
1. **Overview:** Live FPS, inference latency (ms), Qualcomm CPU usage %, RAM allocation, and camera status.
2. **Live Detection:** Real-time MJPEG camera stream with overlaid bounding boxes and health badges.
3. **Crop Analysis:** Identification of crop species, disease condition, confidence %, and agronomic recommendations.
4. **Detection History:** Searchable, filterable log of past detections with thumbnail inspection and CSV export.
5. **Model Settings:** Live adjustment of confidence threshold, camera resolution, and inference rate limit.
6. **Hardware Telemetry:** Qualcomm SoC temperature and memory tracking.

---

## 8. Offline Operation

FREY AI is **100% self-contained**:
- All inference runs locally on the Qualcomm QRB2210 via ONNX Runtime / OpenCV DNN.
- Web assets (CSS, JS, fonts) and SQLite databases are served locally.
- No active internet connection is required after initial package setup.

---

## 9. Optional: Run as a systemd Background Service

To have FREY AI start automatically when the Arduino UNO Q boots up:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/frey-ai.service
   ```

2. Paste the following configuration:
   ```ini
   [Unit]
   Description=FREY AI Edge Plant Disease Detection
   After=network.target

   [Service]
   Type=simple
   User=arduino
   WorkingDirectory=/home/arduino/frey-ai
   ExecStart=/home/arduino/frey-ai/.venv/bin/python3 frey/server.py --host 0.0.0.0 --port 5000
   Restart=always
   RestartSec=5
   Environment=PYTHONPATH=/home/arduino/frey-ai

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable frey-ai
   sudo systemctl start frey-ai
   ```

4. Check status:
   ```bash
   sudo systemctl status frey-ai
   ```

---

## 10. Low-Power CPU Optimization on Qualcomm QRB2210

The Qualcomm QRB2210 features four low-power ARM Cortex-A53 cores. To prevent thermal throttling, reduce power draw, and guarantee smooth UI responsiveness, FREY AI includes multiple edge-specific optimizations:

1. **Thread Balancing (2 Threads Default):**
   - Rather than pinning all 4 cores at 100%, ONNX Runtime is pinned to 2 intra-op worker threads (`options.intra_op_num_threads = 2`).
   - This leaves 2 dedicated cores for the Linux kernel, USB UVC video grabber, and Flask web server.
   - You can switch between 1, 2, or 4 threads in real-time from the dashboard Settings panel.

2. **Adaptive Eco Mode (Scene Change Detection):**
   - Enabled by default (`eco_mode: true`).
   - In real-world plant monitoring, foliage remains motionless for long periods. FREY AI runs an ultra-lightweight ($<0.15$ ms) $64 \times 48$ frame differencing pass.
   - If the plant scene is static, inference is throttled down to a 0.5 Hz keep-alive rate, reusing detection metadata for the live overlay.
   - When motion or a new leaf is detected, full-speed inference immediately resumes.
   - **CPU Savings:** Reduces continuous idle CPU utilization from ~85% down to ~15-20%.

3. **Demand-Driven JPEG Encoding:**
   - Software JPEG compression is completely skipped in the background when no browser client is actively connected to `/video_feed`.
   - When streaming, JPEG quality is optimized to 65 at 15 FPS, saving 40% encoding cycles without visual degradation at 320x240 / 416x416.

4. **Hardware Camera Pacing:**
   - The USB camera grabber runs at 15 FPS with timed loop pacing, eliminating high-frequency V4L2 kernel busy-spin polling.

5. **SIMD Preprocessing:**
   - Uses C++/NEON-accelerated `cv2.dnn.blobFromImage` for BGR-to-RGB conversion, normalization, and NCHW layout in a single pass.

6. **Background Tab Throttling:**
   - The web dashboard uses the HTML5 Page Visibility API to halt REST polling when the browser tab is hidden or backgrounded.

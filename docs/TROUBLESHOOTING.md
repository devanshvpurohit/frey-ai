# FREY AI — Edge Troubleshooting & Diagnostics

This guide covers common edge hardware, camera, runtime, and Linux issues encountered when deploying on the **Arduino UNO Q** (Qualcomm QRB2210 / Debian 13).

---

## 1. USB Camera Issues

### A. Camera Disconnects or Freezes ("USB Failure")
**Symptom:** Live video stops updating, or `/dev/video0` disappears.  
**Cause:** USB voltage drop, loose connector, or UVC driver timeout.  
**Built-in Solution in FREY AI:**
- FREY AI implements an automatic reconnect state machine with exponential backoff.
- If consecutive frame read failures exceed 5, the hardware device is cleanly released and re-initialized.
- If no physical camera is accessible after 3 attempts, the system automatically falls back to an animated synthetic test canopy pattern with a diagnostic banner, preventing server crashes.

**Manual Verification:**
```bash
# Check if kernel sees the USB device
lsusb
dmesg | grep -i uvc

# Check V4L2 device nodes
ls -l /dev/video*
```

### B. "Permission Denied" on `/dev/video0`
**Cause:** Current Linux user lacks membership in the `video` group.  
**Fix:**
```bash
sudo usermod -aG video $USER
# Log out and log back in, or run:
newgrp video
```

### C. Device Busy ("EBUSY" / Resource Temporarily Unavailable)
**Cause:** Another process (e.g. OpenCV script, ffmpeg, or Arduino App Lab) is already holding the camera.  
**FREY AI Protection:**
- FREY AI utilizes a file-based lock (`/tmp/frey_camera.lock`) with `fcntl.flock(LOCK_EX | LOCK_NB)`.
- If an existing process holds the lock, FREY AI logs a warning and releases gracefully.
**To clear stale locks:**
```bash
# Find and terminate rogue camera processes
fuser -v /dev/video0
sudo rm -f /tmp/frey_camera.lock
```

### D. Selecting `/dev/video1` or `/dev/video2`
Many modern USB webcams register multiple nodes (e.g. `/dev/video0` for video frames and `/dev/video1` for metadata/h264).
If `/dev/video0` produces black frames, open the FREY AI Dashboard, navigate to **Edge AI & Device Settings**, change the camera device to `/dev/video1` or `/dev/video2`, and click **Apply Settings**.

---

## 2. Debian 13 PEP 668 & Python Package Conflicts

### Symptom: `error: externally-managed-environment`
```
hint: This environment is externally managed
hint: To install Python packages system-wide, try apt install
```
**Cause:** Debian 13 enforces PEP 668 to prevent arbitrary `pip install` commands from overwriting core OS packages.  
**Correct Solution (Applied in FREY AI):**
Never use `--break-system-packages`. Instead:
1. Use Debian's pre-packaged wheels:
   ```bash
   sudo apt-get install -y python3-opencv python3-numpy python3-flask
   ```
2. Create an isolated virtual environment with access to system packages:
   ```bash
   python3 -m venv --system-site-packages .venv
   source .venv/bin/activate
   ```

---

## 3. Inference Engine Backend: ONNX Runtime vs. OpenCV DNN

FREY AI includes a **universal dual-backend architecture**:
1. **Primary Backend:** `onnxruntime` using `CPUExecutionProvider` (multi-threaded).
2. **Fallback Backend:** `cv2.dnn.readNetFromONNX()` using Debian's native OpenCV DNN engine.

If `pip install onnxruntime` fails on Qualcomm aarch64 due to missing pre-built wheels:
- **No problem:** FREY AI automatically detects the absence of `onnxruntime` and falls back to `cv2.dnn`.
- OpenCV DNN requires **zero extra pip dependencies** because it uses Debian's `python3-opencv` package.
- The dashboard will display `OPENCV_DNN` in the AI Inference card.

---

## 4. Qualcomm QRB2210 Thermal & CPU Management

The Qualcomm QRB2210 is a power-efficient quad-core ARM Cortex-A53 processor. Continuous computer vision inference can cause thermal throttling if unconstrained.

### Performance Target
- **Inference Rate:** Configured to **2–5 FPS** (not a high-frame rate gaming engine).
- **Camera Resolution:** Defaulting to **$320 \times 240$** reduces memory bandwidth by 75% compared to 720p while maintaining sufficient detail for the $416 \times 416$ YOLO input.

### If CPU Usage Exceeds 85% or Temperature Exceeds 70°C:
1. Open the FREY AI Dashboard.
2. In the **Edge AI & Device Settings** panel, adjust the **Inference Rate Limit** slider down to **2.0 Hz** or **1.5 Hz**.
3. Ensure the Arduino UNO Q has adequate ambient ventilation or a small heatsink attached to the Qualcomm SoC shielding.

---

## 5. Agronomic Safety & Classification Sanity Checks

### "Why is my plant marked as Diseased when the leaf is only dry?"
- Neural network object detectors evaluate visual patterns (color, necrotic margins, pustules). Moisture stress, scorch, or nutrient deficiencies can visually mimic fungal blights.
- **Rule:** FREY AI confidence scores represent *classification certainty*, not biological disease severity. Always verify symptoms with in-field manual inspection before applying chemical controls.

### "Why is a plant with zero detections not marked as Healthy?"
- An absence of detections simply means no leaf was confidently detected in the camera frame.
- Marking an empty frame as "Healthy" would represent a dangerous false negative for crop scouting.
- FREY AI explicitly reports: `No Canopy Identified / Awaiting foliage detection`.

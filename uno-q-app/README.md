# FREY AI — Multi-Crop Plant Disease Detection App
### Official Arduino App Lab Package for Arduino UNO Q

**FREY AI** is an edge-AI agricultural computer vision application that detects and classifies plant diseases across 13 crop species using an Ultralytics YOLO11n ONNX model running on the **Qualcomm QRB2210 Linux MPU**, paired with real-time status indication and hardware controls on the **STM32 MCU**.

---

## 1. Hardware Setup

1. **Vision:** Connect any standard USB UVC webcam to the USB port of the Arduino UNO Q.
2. **Power:** 5V / 3A USB-C power adapter.
3. **Optional Hardware Controls:**
   - **Pin 2 (INPUT_PULLUP):** Connect a momentary push-button to ground for physical one-touch field snapshot triggers.
   - **Pin 7 (OUTPUT):** Connect an optional red LED or piezo buzzer for physical audio/visual alert upon disease detection.
   - **Pin 13 (Built-in LED):** Automatic heartbeat and pathology status indicator:
     - *Gentle 1 Hz blink:* System active, scanning camera field.
     - *Solid ON:* Verified healthy foliage in view.
     - *Fast strobe:* Pathogenic foliar lesion detected.

---

## 2. Running in Arduino App Lab

1. Launch **Arduino App Lab**.
2. Select **Open App** and choose this `uno-q-app` directory.
3. Click the **Run** button (▶️).
   - App Lab will automatically build and flash `sketch/sketch.ino` to the Arduino microcontroller core.
   - App Lab will spin up the Python environment for `python/main.py`.
   - The Flask REST API and live dashboard will automatically become available on port **5000**.
4. Click the **Open Web UI** button or navigate to:
   ```
   http://<UNO_Q_IP_ADDRESS>:5000
   ```

---

## 3. Features Available in the Dashboard

- **Live Camera Stream:** Continuous MJPEG video feed with real-time bounding boxes and health badges.
- **Crop Analysis:** Automated identification of crop species (Banana, Chilli, Cauliflower, Groundnut, Radish, etc.), condition, classification certainty %, and recommended agronomic actions.
- **Detection History:** Filterable table of past detections with snapshot image popups and CSV export.
- **Model Settings:** Adjust confidence threshold (10%–95%), inference rate limit, camera device, resolution, and CPU thread count on the fly.
- **Eco Mode (Adaptive Power Saver):** Automatically reduces inference frequency on static foliage, dropping idle CPU utilization by ~80%.
- **Hardware Telemetry:** Qualcomm SoC CPU utilization, RAM pool allocation, and SoC temperature.

---

## 4. Architecture

```
 Arduino UNO Q
  ├── Qualcomm QRB2210 Linux (MPU)
  │    ├── python/main.py (App Lab Entrypoint)
  │    ├── frey/ (Inference, Camera Grabber, Database, Flask REST API)
  │    └── models/ (Ultralytics YOLO11n ONNX 416x416)
  │
  └── STM32 Real-Time Microcontroller (MCU)
       ├── sketch/sketch.ino (Heartbeat, Button Trigger, Alarm Relay)
       └── Arduino App Lab RPC Bridge
```

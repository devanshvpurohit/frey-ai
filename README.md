# FREY AI — Multi-Crop Plant Disease Detection on Arduino UNO Q

**FREY AI** is a complete, self-contained edge-AI agricultural computer vision system designed to detect and classify plant diseases across multiple crop species in real time on the **Arduino UNO Q** (4GB RAM, Qualcomm QRB2210 Linux processor) with a standard USB UVC webcam.

```
       +-------------------------------------------------------------+
       |                      ARDUINO UNO Q (4GB)                    |
       |                                                             |
       |  +--------------------+         +------------------------+  |
       |  |   USB UVC Camera   |         |   Qualcomm QRB2210     |  |
       |  |  (/dev/video0..2)  | ------> |  quad-core ARM Cortex  |  |
       |  |   V4L2 Grabber     |         |  Debian GNU/Linux 13   |  |
       |  +--------------------+         +------------------------+  |
       |                                              |              |
       |                                              v              |
       |                                 +------------------------+  |
       |                                 |   YOLO11n ONNX Engine  |  |
       |                                 |   (416x416 / Opset 12) |  |
       |                                 +------------------------+  |
       |                                              |              |
       |                                              v              |
       |  +-------------------------------------------------------+  |
       |  |             FREY AI Edge Server (Port 5000)           |  |
       |  |   Flask REST API  *  MJPEG Stream  *  SQLite History  |  |
       |  |       Industrial Dark Green & Lime Web Dashboard      |  |
       |  +-------------------------------------------------------+  |
       +-------------------------------------------------------------+
```

---

## Key Highlights

- **Edge-Native Inference:** Runs on the **Qualcomm QRB2210 quad-core ARM processor** running Debian GNU/Linux 13. AI inference runs strictly on the Linux processor—**not** on the STM32 microcontroller.
- **No Cloud or High-Power Host Required:** Operates 100% offline at the field edge without Ollama, cloud APIs, ESP32, or external coprocessors.
- **Resilient USB Camera Pipeline:** Supports `/dev/video0`, `/dev/video1`, and `/dev/video2` with automatic reconnection, frame buffering, single-process file locking, and synthetic fallback when physical cameras are unplugged.
- **Dual Inference Engine Support:** Universal compatibility with both **ONNX Runtime** (`CPUExecutionProvider`) and **OpenCV DNN** (`cv2.dnn.readNetFromONNX`), gracefully falling back with zero user intervention.
- **Debian 13 PEP 668 Compliant:** Uses native Debian apt packages (`python3-opencv`, `python3-numpy`, `python3-flask`) inside an isolated `--system-site-packages` environment. Never modifies system Python unsafely.
- **Agronomic Safety Protocols:** Enforces that confidence percentages reflect model probability, *never* biological disease severity, and prevents declaring a plant healthy simply because no detection was produced.

---

## 1. Supported Taxonomy (13 Crops, 29 Classes)

FREY AI supports the canonical **PlantDoc** object detection taxonomy and provides an extensible registry for adding new crops (Rice, Wheat, Cotton, Maize, Chilli, etc.):

| Crop Species | Supported Health & Disease Categories |
|:---|:---|
| **Apple** | Healthy Leaf, Apple Scab, Cedar Apple Rust |
| **Bell Pepper** | Healthy Leaf, Bacterial Leaf Spot |
| **Blueberry** | Healthy Leaf |
| **Cherry** | Healthy Leaf |
| **Corn (Maize)** | Gray Leaf Spot, Northern Leaf Blight, Common Rust |
| **Grape** | Healthy Leaf, Black Rot |
| **Peach** | Healthy Leaf |
| **Potato** | Healthy Leaf, Early Blight, Late Blight |
| **Raspberry** | Healthy Leaf |
| **Soybean** | Healthy Leaf |
| **Squash** | Powdery Mildew |
| **Strawberry** | Healthy Leaf |
| **Tomato** | Healthy Leaf, Early Blight, Late Blight, Septoria Leaf Spot, Bacterial Spot, Mosaic Virus, Yellow Leaf Curl, Leaf Mold, Spider Mites |

---

## 2. Project Structure

```
frey-ai/
  training/
    prepare_dataset.py    # Dataset download, sanitization, VOC-to-YOLO converter
    train.py              # YOLO11n training script with leaf augmentations
    evaluate.py           # Precision, recall, mAP50, mAP50-95, confusion matrix
    export_onnx.py        # ONNX export, graph verification, tensor inspection
    data.yaml             # YOLO dataset configuration
    taxonomy.py           # Shared canonical taxonomy and agronomic registry
  deployment/
    frey/
      __init__.py
      camera.py           # Threaded V4L2 USB camera grabber & reconnect logic
      detector.py         # Agronomic wrapper, bounding box & badge annotator
      inference.py        # ONNX Runtime & OpenCV DNN dual inference engine
      database.py         # SQLite detection history & telemetry manager
      server.py           # Flask REST API backend & MJPEG video streamer
      system_monitor.py   # Qualcomm QRB2210 CPU, RAM, & thermal sensor reader
      taxonomy.py         # Agronomic metadata & treatment recommendations
    models/
      frey_yolo11n_416.onnx  # Fixed 416x416 ONNX detection model
      classes.json           # Class mapping metadata
      model_metadata.json    # Tensor shape & hardware specs
    data/
      frey.db             # Local SQLite database
      snapshots/          # Saved detection image files
    templates/
      index.html          # Responsive dark green / lime dashboard
    static/
      css/style.css       # Professional agricultural theme stylesheet
      js/app.js           # Real-time telemetry, live stream & history controller
    setup_board.sh        # Debian 13 PEP 668 automated setup script
    start_frey.sh         # Daemon start script
    stop_frey.sh          # Daemon stop script
    requirements-board.txt
  docs/
    TRAINING.md           # In-depth training & fine-tuning instructions
    DEPLOYMENT.md         # Step-by-step Arduino UNO Q setup & systemd service
    TROUBLESHOOTING.md    # Camera reconnect, thermal, & PEP 668 diagnostics
  README.md
```

---

## 3. Quick Start: Training Pipeline (Host PC/Mac)

```bash
cd frey-ai/training

# Step 1: Generate synthetic verification dataset or ingest PlantDoc
python3 prepare_dataset.py --synthetic-sample

# Step 2: Train YOLO11n (auto-detects MPS / CUDA / CPU)
python3 train.py --epochs 30 --batch 16 --imgsz 416

# Step 3: Evaluate model metrics
python3 evaluate.py --weights runs/train/frey_yolo11n/weights/best.pt

# Step 4: Export to fixed 416x416 ONNX for Arduino UNO Q
python3 export_onnx.py --weights runs/train/frey_yolo11n/weights/best.pt
```

---

## 4. Quick Start: Arduino UNO Q Deployment

### 1. Copy Files to the Board
```bash
scp -r frey-ai/deployment/* root@<UNO_Q_IP_ADDRESS>:/home/arduino/frey-ai/
```

### 2. Run Board Setup (Debian 13 PEP 668 Compliant)
```bash
ssh root@<UNO_Q_IP_ADDRESS>
cd /home/arduino/frey-ai
chmod +x setup_board.sh start_frey.sh stop_frey.sh
./setup_board.sh
```

### 3. Start the FREY AI Service
```bash
./start_frey.sh
```

### 4. Access the Dashboard
Open your browser and navigate to:
```
http://<UNO_Q_IP_ADDRESS>:5000
```

---

## 5. REST API Endpoints

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/` | `GET` | Main interactive web dashboard |
| `/video_feed` or `/api/stream` | `GET` | Multipart MJPEG stream with overlaid detections |
| `/api/status` | `GET` | Camera, model, CPU, RAM, temperature & detection stats |
| `/api/detections` | `GET` | Live detections from the latest frame with taxonomy |
| `/api/history` | `GET` | Paginated, filterable historical detection log |
| `/api/settings` | `GET` | Current configuration & discovered `/dev/video*` devices |
| `/api/settings` | `POST` | Update threshold, camera device, or inference rate |
| `/api/camera/start` | `POST` | Start/restart camera capture worker |
| `/api/camera/stop` | `POST` | Pause camera capture worker |
| `/api/snapshot` | `POST` | Trigger and save manual high-resolution inspection frame |
| `/api/crops` | `GET` | Full list of supported crop species and diseases |

---

## 6. Verification & Validation Checklist

- [x] Fixed 416x416 input shape matches ONNX model graph (`[1, 3, 416, 416]`).
- [x] Output tensor dimensions (`[1, 84, 3549]` or `[1, 33, 3549]`) correctly parsed by NMS post-processor.
- [x] Dual backend fallback: ONNX Runtime CPU $\leftrightarrow$ OpenCV DNN verified.
- [x] USB camera reconnection logic with exponential backoff and lock handling.
- [x] Synthetic test pattern generator for headless or zero-camera operation.
- [x] Thread-safe SQLite persistence for detection events and hardware metrics.
- [x] Responsive dark green & lime dashboard with live video, crop analysis, history, settings, and hardware telemetry.

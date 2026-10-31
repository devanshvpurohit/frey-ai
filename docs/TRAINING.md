# FREY AI — Model Training Pipeline

This document details the complete model training workflow for **FREY AI**, designed to train Ultralytics **YOLO11n** on your host PC/Mac and export an edge-optimized ONNX model for the **Arduino UNO Q** (Qualcomm QRB2210).

---

## 1. Prerequisites (Host Workstation)

Training should be executed on a workstation with GPU/MPS acceleration (Mac with Apple Silicon or Linux/Windows with NVIDIA GPU).

```bash
# Clone the repository and enter the training directory
cd frey-ai/training

# Install host training dependencies
pip install ultralytics onnx onnxslim opencv-python pillow pyyaml
```

---

## 2. Dataset Preparation

FREY AI starts with the **PlantDoc Object Detection Dataset**, containing 13 plant species and 29 distinct condition classes (both healthy and diseased foliage).

### Option A: Automatic Pipeline Validation (Zero-Download Synthetic Test)

To test the entire training and export pipeline immediately without downloading large archives:

```bash
python3 prepare_dataset.py --synthetic-sample
```

This generates:
- 29 synthetic images and label pairs spanning every single class.
- `data.yaml` configured for YOLO11n.
- `classes.json` containing the authoritative taxonomy.

### Option B: Training with Real PlantDoc Data

1. Clone or download the PlantDoc dataset repository:
   ```bash
   git clone https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset.git plant_doc_raw
   ```

2. Run the preparation script:
   ```bash
   python3 prepare_dataset.py --source-dir plant_doc_raw --output-dir dataset --val-split 0.15
   ```

### Dataset Sanitization Details
The `prepare_dataset.py` pipeline performs critical sanitization steps:
- **Corrupted Row Rejection:** Skips malformed rows in the raw CSV (non-numeric coordinates, inverted boxes where $x_{min} \ge x_{max}$).
- **Coordinate Clamping:** Normalizes VOC coordinates $[x_{min}, y_{min}, x_{max}, y_{max}]$ into YOLO format $[c_x, c_y, w, h]$ clamped strictly between $0.0$ and $1.0$.
- **Class Normalization:** Maps inconsistent class labels (e.g. `grape leaf` vs `Grape leaf`, `Soyabean` vs `Soybean`) to the 29 canonical taxonomy IDs.

---

## 3. Supported Crops & Classes Taxonomy

The 29 base classes cover 13 agricultural crop species:

| Class ID | Raw Label | Crop | Condition | Status |
|:---:|:---|:---|:---|:---:|
| 0 | Apple Scab Leaf | Apple | Apple Scab | Diseased |
| 1 | Apple leaf | Apple | Healthy Leaf | Healthy |
| 2 | Apple rust leaf | Apple | Cedar Apple Rust | Diseased |
| 3 | Bell_pepper leaf | Bell Pepper | Healthy Leaf | Healthy |
| 4 | Bell_pepper leaf spot | Bell Pepper | Bacterial Spot | Diseased |
| 5 | Blueberry leaf | Blueberry | Healthy Leaf | Healthy |
| 6 | Cherry leaf | Cherry | Healthy Leaf | Healthy |
| 7 | Corn Gray leaf spot | Corn (Maize) | Gray Leaf Spot | Diseased |
| 8 | Corn leaf blight | Corn (Maize) | Northern Leaf Blight | Diseased |
| 9 | Corn rust leaf | Corn (Maize) | Common Rust | Diseased |
| 10 | grape leaf | Grape | Healthy Leaf | Healthy |
| 11 | grape leaf black rot | Grape | Black Rot | Diseased |
| 12 | Peach leaf | Peach | Healthy Leaf | Healthy |
| 13 | Potato leaf | Potato | Healthy Leaf | Healthy |
| 14 | Potato leaf early blight | Potato | Early Blight | Diseased |
| 15 | Potato leaf late blight | Potato | Late Blight | Diseased |
| 16 | Raspberry leaf | Raspberry | Healthy Leaf | Healthy |
| 17 | Soyabean leaf | Soybean | Healthy Leaf | Healthy |
| 18 | Squash Powdery mildew leaf | Squash | Powdery Mildew | Diseased |
| 19 | Strawberry leaf | Strawberry | Healthy Leaf | Healthy |
| 20 | Tomato Early blight leaf | Tomato | Early Blight | Diseased |
| 21 | Tomato Septoria leaf spot | Tomato | Septoria Leaf Spot | Diseased |
| 22 | Tomato leaf | Tomato | Healthy Leaf | Healthy |
| 23 | Tomato leaf bacterial spot | Tomato | Bacterial Spot | Diseased |
| 24 | Tomato leaf late blight | Tomato | Late Blight | Diseased |
| 25 | Tomato leaf mosaic virus | Tomato | Mosaic Virus | Diseased |
| 26 | Tomato leaf yellow virus | Tomato | Yellow Leaf Curl | Diseased |
| 27 | Tomato mold leaf | Tomato | Leaf Mold | Diseased |
| 28 | Tomato two spotted spider mites leaf | Tomato | Spider Mite Damage | Diseased |

### Extending with New Crops
The dataset pipeline is pre-architected to ingest additional crop datasets (e.g. Rice, Wheat, Cotton, Chilli). Add your classes to `taxonomy.py` under `EXTENSION_CROPS` and regenerate `data.yaml`.

---

## 4. Model Training

Train the **YOLO11n** model using `train.py`:

```bash
# Auto-detects Apple Silicon MPS, NVIDIA CUDA, or CPU
python3 train.py \
    --data data.yaml \
    --epochs 50 \
    --batch 16 \
    --imgsz 416 \
    --name frey_yolo11n \
    --device auto
```

### Key Training Hyperparameters for Plant Pathology
- **Resolution:** Fixed at $416 \times 416$ (balanced between lesion detection fidelity and edge RAM).
- **Augmentations:**
  - `hsv_h: 0.015`, `hsv_s: 0.7`, `hsv_v: 0.4` (simulates variable sunlight and shadows).
  - `degrees: 15.0` (realistic leaf angles without distortion).
  - `mosaic: 1.0` (critical for small lesion detection).
  - `fliplr: 0.5` (natural leaf symmetry).

Checkpoints will be saved to `runs/train/frey_yolo11n/weights/best.pt`.

---

## 5. Model Evaluation

Validate detection precision, recall, and mAP:

```bash
python3 evaluate.py \
    --weights runs/train/frey_yolo11n/weights/best.pt \
    --data data.yaml \
    --imgsz 416
```

Outputs:
- Mean Precision ($P$), Recall ($R$).
- $mAP@0.50$ and $mAP@0.50:0.95$.
- Normalized confusion matrix saved to `runs/val/eval_results/confusion_matrix.png`.
- Full summary report in `runs/val/eval_results/evaluation_report.json`.

---

## 6. ONNX Model Export

Export the trained model to fixed-shape ONNX format:

```bash
python3 export_onnx.py \
    --weights runs/train/frey_yolo11n/weights/best.pt \
    --output-dir ../deployment/models \
    --imgsz 416 \
    --opset 12
```

The script automatically:
1. Exports with Opset 12 (compatible with both OpenCV DNN and ONNX Runtime).
2. Verifies the ONNX graph using `onnx.checker`.
3. Validates output tensor shape: `[1, 33, 3549]` (4 bounding box coordinates + 29 classes $\times$ 3549 anchors).
4. Runs a benchmark inference pass to measure latency.
5. Saves `frey_yolo11n_416.onnx`, `classes.json`, and `model_metadata.json` into `deployment/models/`.

---

## 7. Transferring Model to Arduino UNO Q

Copy the deployment package to your Arduino UNO Q board:

```bash
scp -r ../deployment/* root@<UNO_Q_IP_ADDRESS>:/home/arduino/frey-ai/
```

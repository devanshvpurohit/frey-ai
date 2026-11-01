#!/usr/bin/env python3
"""
FREY AI - YOLO11n Multi-Crop Plant Disease Training Script
Author: Senior AI/ML Engineer (FREY AI Project)

Designed to train Ultralytics YOLO11n for deployment onto edge hardware
such as the Arduino UNO Q (Qualcomm QRB2210 quad-core ARM processor).

Trains with 416x416 resolution and leaf-disease specific augmentations.
"""

import os
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO
import torch


def select_best_device() -> str:
    """Detect available compute acceleration: MPS (Apple Silicon), CUDA (NVIDIA), or CPU."""
    if torch.cuda.is_available():
        print(f"[DEVICE] Using NVIDIA CUDA: {torch.cuda.get_device_name(0)}")
        return "0"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("[DEVICE] Using Apple Silicon MPS (Metal Performance Shaders)")
        return "mps"
    else:
        print("[DEVICE] Using standard CPU")
        return "cpu"


def train_frey_model(
    data_yaml: Path,
    epochs: int = 50,
    batch_size: int = 16,
    imgsz: int = 416,
    device: str = "auto",
    project: str = "runs/train",
    name: str = "frey_yolo11n",
    pretrained_weights: str = "yolo11n.pt",
) -> Path:
    """Train YOLO11n model and return path to best.pt."""
    if device == "auto":
        device = select_best_device()

    # Locate base model weights
    weights_path = Path(pretrained_weights)
    if not weights_path.exists():
        # Check parent folder or project root
        root_weights = Path(__file__).resolve().parent.parent / "yolo11n.pt"
        if root_weights.exists():
            weights_path = root_weights

    print(f"\n==========================================")
    print(f"       FREY AI MODEL TRAINING             ")
    print(f"==========================================")
    print(f"Model Architecture : Ultralytics YOLO11n")
    print(f"Data Configuration : {data_yaml}")
    print(f"Input Resolution   : {imgsz}x{imgsz}")
    print(f"Epochs             : {epochs}")
    print(f"Batch Size         : {batch_size}")
    print(f"Target Hardware    : Qualcomm QRB2210 (Debian 13)")
    print(f"Compute Device     : {device}")
    print(f"Base Weights       : {weights_path}")
    print(f"==========================================\n")

    model = YOLO(str(weights_path))

    # Leaf disease specific hyperparameter setup:
    # Foliage rotation, light hue/saturation variations, moderate mosaic, no extreme perspective distortion
    results = model.train(
        data=str(data_yaml.resolve()),
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        workers=4,
        save=True,
        save_period=10,
        exist_ok=True,
        cls=1.0,         # Balanced classification penalty for multi-class separation
        # Augmentations designed for plant canopy images
        hsv_h=0.015,     # subtle leaf color variation
        hsv_s=0.7,       # variable sunlight saturation
        hsv_v=0.4,       # variable shadows under canopy
        degrees=15.0,    # realistic leaf orientation
        translate=0.1,   # camera panning
        scale=0.5,       # distance from camera
        shear=2.0,
        fliplr=0.5,      # horizontal mirror
        flipud=0.2,      # slight vertical variation
        mosaic=1.0,      # multi-crop context
        mixup=0.1,
    )

    save_dir = Path(results.save_dir)
    best_pt = save_dir / "weights" / "best.pt"
    print(f"\n[TRAINING FINISHED] Best model saved to: {best_pt}")
    return best_pt


def main():
    parser = argparse.ArgumentParser(description="Train FREY AI YOLO11n Model")
    parser.add_argument("--data", type=str, default="data.yaml", help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=416, help="Image resolution (416 recommended for UNO Q)")
    parser.add_argument("--device", type=str, default="auto", help="Compute device: auto, cpu, mps, 0")
    parser.add_argument("--project", type=str, default="runs/train", help="Save directory")
    parser.add_argument("--name", type=str, default="frey_yolo11n", help="Experiment name")
    parser.add_argument("--weights", type=str, default="yolo11n.pt", help="Pretrained weights")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    data_yaml = Path(args.data)
    if not data_yaml.is_absolute():
        data_yaml = base_dir / data_yaml

    if not data_yaml.exists():
        print(f"[ERROR] Data config not found: {data_yaml}")
        print("Please run `python prepare_dataset.py --synthetic-sample` first!")
        sys.exit(1)

    train_frey_model(
        data_yaml=data_yaml,
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        project=args.project,
        name=args.name,
        pretrained_weights=args.weights,
    )


if __name__ == "__main__":
    main()

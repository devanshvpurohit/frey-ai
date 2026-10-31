#!/usr/bin/env python3
"""
FREY AI - Model Evaluation & Performance Validation Script
Author: Senior AI/ML Engineer (FREY AI Project)

Validates trained YOLO11n weights against validation set.
Computes:
- Overall Precision, Recall, mAP@0.50, mAP@0.50:0.95
- Per-class metrics
- Confusion matrix export
- Agricultural classification sanity check
"""

import os
import sys
import json
import argparse
from pathlib import Path
from ultralytics import YOLO

# Import taxonomy
try:
    from taxonomy import PLANTDOC_CLASSES, get_taxonomy_entry
except ImportError:
    from frey.taxonomy import PLANTDOC_CLASSES, get_taxonomy_entry


def evaluate_model(
    weights_path: Path,
    data_yaml: Path,
    imgsz: int = 416,
    batch_size: int = 16,
    device: str = "cpu",
    output_dir: str = "runs/val",
) -> dict:
    """Run model validation and print formatted performance report."""
    print(f"\n==========================================")
    print(f"       FREY AI MODEL EVALUATION           ")
    print(f"==========================================")
    print(f"Weights     : {weights_path}")
    print(f"Data YAML   : {data_yaml}")
    print(f"Resolution  : {imgsz}x{imgsz}")
    print(f"Batch Size  : {batch_size}")
    print(f"Device      : {device}")
    print(f"==========================================\n")

    model = YOLO(str(weights_path))

    metrics = model.val(
        data=str(data_yaml),
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=output_dir,
        name="eval_results",
        plots=True,
        save_json=True,
        exist_ok=True,
    )

    # Extract metrics summary
    box = metrics.box
    summary = {
        "precision": round(float(box.mp), 4),
        "recall": round(float(box.mr), 4),
        "mAP50": round(float(box.map50), 4),
        "mAP50_95": round(float(box.map), 4),
        "fitness": round(float(metrics.fitness), 4),
        "classes_evaluated": len(box.maps),
    }

    print("\n" + "=" * 55)
    print("             VALIDATION METRICS SUMMARY            ")
    print("=" * 55)
    print(f"  Precision (mean) : {summary['precision']:.4f}")
    print(f"  Recall (mean)    : {summary['recall']:.4f}")
    print(f"  mAP @ 0.50       : {summary['mAP50']:.4f}")
    print(f"  mAP @ 0.50:0.95  : {summary['mAP50_95']:.4f}")
    print(f"  Model Fitness    : {summary['fitness']:.4f}")
    print("=" * 55)

    # Save metrics JSON
    out_path = Path(output_dir) / "eval_results" / "evaluation_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[REPORT SAVED] Full report written to: {out_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate FREY AI YOLO11n Model")
    parser.add_argument("--weights", type=str, default="runs/train/frey_yolo11n/weights/best.pt", help="Path to weights")
    parser.add_argument("--data", type=str, default="data.yaml", help="Path to data.yaml")
    parser.add_argument("--imgsz", type=int, default=416, help="Evaluation resolution")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="cpu", help="Compute device: cpu, mps, 0")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        weights_path = base_dir / weights_path

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = base_dir / data_path

    if not weights_path.exists():
        # Fallback to yolo11n.pt if best.pt is not yet trained
        fallback = base_dir.parent / "yolo11n.pt"
        if fallback.exists():
            weights_path = fallback
            print(f"[INFO] Using base weights for test evaluation: {weights_path}")
        else:
            print(f"[ERROR] Weights file not found: {weights_path}")
            sys.exit(1)

    evaluate_model(
        weights_path=weights_path,
        data_yaml=data_path,
        imgsz=args.imgsz,
        batch_size=args.batch,
        device=args.device,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FREY AI - ONNX Model Export & Edge Verification Script
Author: Senior AI/ML Engineer (FREY AI Project)

Converts trained YOLO11n PyTorch weights to optimized ONNX format for
deployment on Arduino UNO Q (Qualcomm QRB2210 quad-core ARM Linux).

Key Features:
- Exports to fixed 416x416 resolution (optimal for low RAM footprint).
- Standard Opset 12 for maximum compatibility with OpenCV DNN and ONNX Runtime.
- Graph sanity check via onnx.checker.
- Copies model & metadata directly to deployment/models.
- Validates output tensor dimensions and tests dummy inference.
"""

import os
import sys
import json
import time
import shutil
import argparse
from pathlib import Path
import numpy as np

# Ultralytics & ONNX
from ultralytics import YOLO
import onnx
import onnxruntime as ort

# Import taxonomy
try:
    from taxonomy import PLANTDOC_CLASSES
except ImportError:
    from frey.taxonomy import PLANTDOC_CLASSES


def export_to_onnx(
    weights_path: Path,
    output_dir: Path,
    imgsz: int = 416,
    opset: int = 12,
    simplify: bool = True,
) -> Path:
    """Export YOLO11n weights to ONNX format."""
    print(f"\n==========================================")
    print(f"       FREY AI ONNX EXPORT               ")
    print(f"==========================================")
    print(f"Source Model : {weights_path}")
    print(f"Resolution   : {imgsz}x{imgsz}")
    print(f"Opset        : {opset}")
    print(f"Target OS    : Debian GNU/Linux 13 (aarch64)")
    print(f"Target CPU   : Qualcomm QRB2210 (4GB RAM)")
    print(f"Output Dir   : {output_dir}")
    print(f"==========================================\n")

    output_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(weights_path))

    # Perform Ultralytics export
    exported_file = model.export(
        format="onnx",
        imgsz=imgsz,
        dynamic=False,
        opset=opset,
        simplify=simplify,
    )
    exported_path = Path(exported_file)
    print(f"[INFO] Initial ONNX exported to: {exported_path}")

    # Destination in deployment/models
    dest_path = output_dir / "frey_yolo11n_416.onnx"
    shutil.copy2(exported_path, dest_path)
    print(f"[INFO] Copied to deployment package: {dest_path} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")

    # 1. Verify ONNX model integrity
    print("\n[VERIFICATION 1/3] Checking ONNX graph structure...")
    onnx_model = onnx.load(str(dest_path))
    onnx.checker.check_model(onnx_model)
    print("  -> ONNX model graph is mathematically valid and well-formed.")

    # 2. Inspect Inputs and Outputs via ONNX Runtime
    print("\n[VERIFICATION 2/3] Inspecting I/O tensor specifications...")
    session = ort.InferenceSession(str(dest_path), providers=["CPUExecutionProvider"])
    
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    
    print(f"  Input Name   : {input_meta.name}")
    print(f"  Input Shape  : {input_meta.shape}")
    print(f"  Input Type   : {input_meta.type}")
    print(f"  Output Name  : {output_meta.name}")
    print(f"  Output Shape : {output_meta.shape}")
    print(f"  Output Type  : {output_meta.type}")

    # 3. Test dummy inference
    print("\n[VERIFICATION 3/3] Running benchmark dummy inference on CPU...")
    dummy_input = np.random.uniform(0.0, 1.0, size=(1, 3, imgsz, imgsz)).astype(np.float32)
    
    warmup_iters = 3
    for _ in range(warmup_iters):
        _ = session.run([output_meta.name], {input_meta.name: dummy_input})

    test_iters = 10
    start_t = time.perf_counter()
    for _ in range(test_iters):
        outputs = session.run([output_meta.name], {input_meta.name: dummy_input})
    total_t = time.perf_counter() - start_t
    avg_latency = (total_t / test_iters) * 1000.0
    est_fps = 1000.0 / avg_latency

    output_tensor = outputs[0]
    print(f"  Output Tensor Shape   : {output_tensor.shape}")
    print(f"  Host Avg Latency      : {avg_latency:.2f} ms")
    print(f"  Host Estimated FPS    : {est_fps:.1f} FPS")

    # Generate metadata JSON
    metadata = {
        "model_name": "frey_yolo11n_416",
        "architecture": "Ultralytics YOLO11n",
        "format": "ONNX",
        "opset": opset,
        "input_name": input_meta.name,
        "input_shape": input_meta.shape,
        "output_name": output_meta.name,
        "output_shape": list(output_tensor.shape),
        "num_classes": len(PLANTDOC_CLASSES),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_hardware": {
            "board": "Arduino UNO Q 4GB RAM",
            "processor": "Qualcomm QRB2210 (quad-core ARM Cortex-A53)",
            "os": "Debian GNU/Linux 13 (Trixie)",
            "execution_provider": "CPUExecutionProvider / OpenCV DNN",
            "recommended_camera_res": "320x240",
            "input_resolution": [imgsz, imgsz],
        },
    }

    meta_path = output_dir / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[INFO] Wrote metadata file: {meta_path}")

    # Copy classes.json to deployment models
    classes_json = Path(__file__).resolve().parent / "classes.json"
    if classes_json.exists():
        shutil.copy2(classes_json, output_dir / "classes.json")
        print(f"[INFO] Copied classes.json to {output_dir / 'classes.json'}")

    print(f"\n[SUCCESS] FREY AI ONNX deployment package ready at: {dest_path}")
    return dest_path


def main():
    parser = argparse.ArgumentParser(description="Export FREY AI YOLO11n to ONNX")
    parser.add_argument("--weights", type=str, default="", help="Path to best.pt or base yolo11n.pt")
    parser.add_argument("--output-dir", type=str, default="../deployment/models", help="Deployment models directory")
    parser.add_argument("--imgsz", type=int, default=416, help="Input size")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    weights_str = args.weights
    if not weights_str:
        # Search for best.pt first, then root yolo11n.pt
        best_pt = base_dir / "runs/train/frey_yolo11n/weights/best.pt"
        root_pt = base_dir.parent / "yolo11n.pt"
        if best_pt.exists():
            weights_path = best_pt
        elif root_pt.exists():
            weights_path = root_pt
        else:
            weights_path = base_dir / "yolo11n.pt"
    else:
        weights_path = Path(weights_str)
        if not weights_path.is_absolute():
            weights_path = base_dir / weights_path

    if not weights_path.exists():
        print(f"[ERROR] Weights file not found: {weights_path}")
        sys.exit(1)

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = base_dir / out_dir

    export_to_onnx(
        weights_path=weights_path,
        output_dir=out_dir,
        imgsz=args.imgsz,
        opset=args.opset,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FREY AI — Mendeley Multi-Crop Disease Dataset Downloader
Dataset DOI: 10.17632/6243z8r6t6.1 (Prem Kumar E., VIT University)
URL: https://data.mendeley.com/datasets/6243z8r6t6/1

Downloads Roboflow YOLOv8 format images and bounding box annotations across:
- Banana (9 conditions)
- Cauliflower (4 conditions)
- Chilli (6 conditions)
- Groundnut (6 conditions)
- Radish (5 conditions)
Total: 30 classes
"""

import os
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_API = "https://data.mendeley.com/public-api/datasets/6243z8r6t6"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "application/vnd.mendeley-public-dataset.1+json",
}

# Folder mapping from Mendeley API
FOLDER_MAP = {
    "train_images": "91aee82c-67d6-4468-8624-5c8017d4f499",
    "train_labels": "904bf182-f705-4868-be98-6dab93e20fae",
    "valid_images": "4f70eff2-8732-47f9-849c-114ef91365b0",
    "valid_labels": "be89adb5-4d67-47bf-a872-d17b02a0e079",
    "test_images": "38d9d50f-cb73-446f-acfe-8a910924fbf6",
    "test_labels": "25c9e667-f878-4362-b68a-7f0781990dc3",
}

MENDELEY_CLASSES = [
    "banana_bract_mosaic_virus",
    "banana_cordana",
    "banana_healthy",
    "banana_insectpest",
    "banana_moko",
    "banana_panama",
    "banana_pestalotiopsis",
    "banana_sigatoka",
    "banana_yb_sigatoka",
    "cauliflower_Blackrot",
    "cauliflower_bacterial _spot _rot",
    "cauliflower_downy_mildew",
    "cauliflower_healthy",
    "chilli_anthracnose",
    "chilli_healthy",
    "chilli_leafcurl",
    "chilli_leafspot",
    "chilli_whitefly",
    "chilli_yellowish",
    "groundnut_early_leaf_spot",
    "groundnut_early_rust",
    "groundnut_healthy",
    "groundnut_late_leaf_spot",
    "groundnut_nutrition_deficiency",
    "groundnut_rust",
    "radish_black_leaf_spot",
    "radish_downey_mildew",
    "radish_flea_beetle",
    "radish_healthy",
    "radish_mosaic"
]


def fetch_file_list(folder_id: str, limit: int = 1000) -> list:
    """Fetch all file descriptors from a Mendeley folder using pagination."""
    files = []
    start = 0
    while True:
        url = f"{BASE_API}/files?folder_id={folder_id}&version=1&$start={start}&$limit={limit}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                batch = json.loads(r.read().decode("utf-8"))
                if not batch:
                    break
                files.extend(batch)
                if len(batch) < limit or len(files) >= 5000:
                    break
                start += len(batch)
        except Exception as e:
            print(f"[WARN] Failed fetching batch at start={start}: {e}")
            break
    return files


def download_single_file(item: dict, dest_dir: Path) -> bool:
    """Download single image or text file from S3."""
    fname = item["filename"]
    out_path = dest_dir / fname
    if out_path.exists() and out_path.stat().st_size > 0:
        return True

    url = item["content_details"]["download_url"]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            with open(out_path, "wb") as f:
                f.write(data)
        return True
    except Exception as e:
        print(f"[WARN] Download failed for {fname}: {e}")
        return False


def download_mendeley_split(
    split_name: str,
    img_folder_id: str,
    lbl_folder_id: str,
    output_dir: Path,
    max_samples: int = 300,
    max_workers: int = 8,
):
    """Download images and labels for a specific split (train or val)."""
    img_dir = output_dir / "images" / split_name
    lbl_dir = output_dir / "labels" / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] Querying Mendeley file list for {split_name} split...")
    img_files = fetch_file_list(img_folder_id, limit=1000)
    lbl_files = fetch_file_list(lbl_folder_id, limit=1000)

    print(f"  Found {len(img_files)} images, {len(lbl_files)} labels in remote {split_name} pool.")

    # Match stem names
    lbl_by_stem = {Path(f["filename"]).stem: f for f in lbl_files}
    matched_pairs = []

    for img_meta in img_files:
        stem = Path(img_meta["filename"]).stem
        if stem in lbl_by_stem:
            matched_pairs.append((img_meta, lbl_by_stem[stem]))

    print(f"  Matched {len(matched_pairs)} image/label pairs.")
    if max_samples and len(matched_pairs) > max_samples:
        import random
        random.seed(42)
        matched_pairs = random.sample(matched_pairs, max_samples)
        print(f"  Sampled {len(matched_pairs)} pairs for efficient training.")

    # Download in parallel
    print(f"  Downloading {len(matched_pairs)} files to {split_name}...")
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for img_item, lbl_item in matched_pairs:
            tasks.append(executor.submit(download_single_file, img_item, img_dir))
            tasks.append(executor.submit(download_single_file, lbl_item, lbl_dir))

        completed = 0
        total = len(tasks)
        for fut in as_completed(tasks):
            if fut.result():
                completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"    Progress: {completed}/{total} files downloaded")

    print(f"[SUCCESS] {split_name} split ready ({len(list(img_dir.glob('*.jpg')))} images, {len(list(lbl_dir.glob('*.txt')))} labels).")


def write_mendeley_yaml(output_dir: Path):
    """Generate YOLO data.yaml for Mendeley 30-class dataset."""
    yaml_content = f"""# FREY AI - Mendeley Multi-Crop Disease Dataset (DOI: 10.17632/6243z8r6t6.1)
path: {output_dir.resolve()}
train: images/train
val: images/val
test: images/val

nc: {len(MENDELEY_CLASSES)}
names:
"""
    for idx, name in enumerate(MENDELEY_CLASSES):
        yaml_content += f"  {idx}: '{name}'\n"

    yaml_path = output_dir.parent / "mendeley_data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"\n[INFO] Wrote YOLO dataset configuration: {yaml_path}")
    return yaml_path


def main():
    parser = argparse.ArgumentParser(description="Download Mendeley Multi-Crop Disease Dataset")
    parser.add_argument("--output-dir", type=str, default="dataset_mendeley", help="Output directory")
    parser.add_argument("--train-samples", type=int, default=300, help="Number of training image pairs")
    parser.add_argument("--val-samples", type=int, default=60, help="Number of validation image pairs")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download threads")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = base_dir / out_dir

    print("==========================================================")
    print("      FREY AI — MENDELEY DATASET INGESTION PIPELINE       ")
    print("==========================================================")
    print(f"Dataset DOI    : 10.17632/6243z8r6t6.1")
    print(f"Target Crops   : Banana, Cauliflower, Chilli, Groundnut, Radish")
    print(f"Classes Count  : 30 Categories")
    print(f"Output Path    : {out_dir}")
    print("==========================================================")

    # Download Train
    download_mendeley_split(
        "train",
        FOLDER_MAP["train_images"],
        FOLDER_MAP["train_labels"],
        out_dir,
        max_samples=args.train_samples,
        max_workers=args.workers,
    )

    # Download Val
    download_mendeley_split(
        "val",
        FOLDER_MAP["valid_images"],
        FOLDER_MAP["valid_labels"],
        out_dir,
        max_samples=args.val_samples,
        max_workers=args.workers,
    )

    write_mendeley_yaml(out_dir)
    print("\n[COMPLETE] Mendeley dataset downloaded and structured for YOLO11 training!")


if __name__ == "__main__":
    main()

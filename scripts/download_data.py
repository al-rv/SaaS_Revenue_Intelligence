"""Download Rivalytics raw CSV files into data/raw."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import KAGGLE_DATASET_SLUG, RAW_DATA_DIR, RAW_TABLE_FILES, ensure_directories


def all_files_present() -> bool:
    return all((RAW_DATA_DIR / filename).exists() for filename in RAW_TABLE_FILES.values())


def print_manual_instructions() -> None:
    print("Manual download instructions:")
    print("1) Open the dataset page:")
    print("   https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset")
    print("2) Download and unzip the dataset.")
    print(f"3) Copy CSV files into: {RAW_DATA_DIR}")
    print("4) Ensure these filenames exist:")
    for filename in RAW_TABLE_FILES.values():
        print(f"   - {filename}")


def run_kaggle_download() -> None:
    has_credentials = bool(os.getenv("KAGGLE_USERNAME")) and bool(os.getenv("KAGGLE_KEY"))
    if not has_credentials:
        print("[info] KAGGLE_USERNAME/KAGGLE_KEY not set in environment.")
        print_manual_instructions()
        return

    command = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_DATASET_SLUG,
        "-p",
        str(RAW_DATA_DIR),
        "--unzip",
    ]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("[error] Kaggle CLI not found. Install it with `uv pip install kaggle`.")
        print_manual_instructions()
    except subprocess.CalledProcessError as exc:
        print(f"[error] Kaggle download failed with exit code {exc.returncode}.")
        print_manual_instructions()


def main() -> None:
    ensure_directories()
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if all_files_present():
        print("[ok] All expected raw files already exist. Skipping download.")
        return

    print("[info] Attempting Kaggle download...")
    run_kaggle_download()

    if all_files_present():
        print("[ok] Raw files ready in data/raw.")
    else:
        print("[warn] Dataset download is incomplete.")
        print_manual_instructions()
        raise SystemExit(1)


if __name__ == "__main__":
    main()

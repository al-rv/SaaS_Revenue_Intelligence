"""Validate local environment before running the analytics pipeline"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from src.config import (
    DUCKDB_PATH,
    MIN_PYTHON_VERSION,
    RAW_DATA_DIR,
    RAW_TABLE_FILES,
    REQUIRED_DIRECTORIES,
    REQUIRED_PACKAGES,
    ensure_directories,
    raw_table_path,
)
from src.db import test_connection

def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON_VERSION:
        required = ".".join(str(part) for part in MIN_PYTHON_VERSION)
        actual = ".".join(str(part) for part in sys.version_info[:3])
        raise RuntimeError(
            f"Python {required}+ is required. Current version: {actual}"
        )
    print(f"[ok] Python {sys.version.split()[0]}")


def check_directories() -> None:
    ensure_directories()
    for directory in REQUIRED_DIRECTORIES:
        if not directory.exists():
            raise RuntimeError(f"Missing required directory: {directory}")
    print(f"[ok] Required directories exist ({len(REQUIRED_DIRECTORIES)} checked)")


def check_packages() -> None:
    for package_name in REQUIRED_PACKAGES:
        importlib.import_module(package_name)
    print(f"[ok] Required packages import successfully ({len(REQUIRED_PACKAGES)} checked)")


def check_duckdb() -> None:
    test_connection()
    print(f"[ok] DuckDB connection successful at {DUCKDB_PATH}")


def check_raw_data_files() -> None:
    missing_files = [
        filename
        for filename in RAW_TABLE_FILES.values()
        if not (RAW_DATA_DIR / filename).exists()
    ]
    if missing_files:
        print("[warn] Raw dataset files are not fully present yet:")
        for filename in missing_files:
            print(f"       - {RAW_DATA_DIR / filename}")
        print("[info] Phase 3 will load these files into DuckDB.")
        return

    print(f"[ok] Raw dataset files found ({len(RAW_TABLE_FILES)} tables)")
    for table_name in RAW_TABLE_FILES:
        path = raw_table_path(table_name)
        print(f"       - {table_name}: {path.name}")


def main() -> None:
    print("SaaS Revenue Intelligence - environment check")
    print("-" * 48)
    check_python_version()
    check_directories()
    check_packages()
    check_duckdb()
    check_raw_data_files()
    print("-" * 48)
    print("Environment check passed.")


if __name__ == "__main__":
    main()
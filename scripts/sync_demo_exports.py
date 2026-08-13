"""Sync processed dashboard Parquet exports into the committed demo folder."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DASHBOARD_EXPORTS, DEMO_DATA_DIR, PROCESSED_DATA_DIR, ensure_directories


def sync_demo_exports() -> None:
    """Copy dashboard Parquet files from processed/ into data/demo/."""
    ensure_directories()
    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)

    missing = [
        filename
        for filename in DASHBOARD_EXPORTS
        if not (PROCESSED_DATA_DIR / filename).exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing processed exports. Run `make pipeline` first, then sync demo. "
            f"Missing: {', '.join(missing)}"
        )

    print("Syncing demo dashboard exports:")
    for filename in DASHBOARD_EXPORTS:
        source = PROCESSED_DATA_DIR / filename
        destination = DEMO_DATA_DIR / filename
        shutil.copy2(source, destination)
        print(f" - {destination.relative_to(ROOT)} ({source.stat().st_size:,} bytes)")
    print("Demo sync completed.")


def main() -> None:
    sync_demo_exports()


if __name__ == "__main__":
    main()

"""Export dashboard-ready Parquet files from DuckDB marts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DASHBOARD_EXPORTS, PROCESSED_DATA_DIR, ensure_directories
from src.db import get_connection


def export_table(query: str, output_path: Path) -> int:
    with get_connection(read_only=True) as conn:
        df = conn.execute(query).df()
    df.to_parquet(output_path, index=False)
    return len(df)


def main() -> None:
    ensure_directories()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Exporting dashboard Parquet files:")
    for filename, query in DASHBOARD_EXPORTS.items():
        output_path = PROCESSED_DATA_DIR / filename
        rows = export_table(query, output_path)
        print(f" - {filename}: {rows} rows")

    print("Dashboard export completed.")


if __name__ == "__main__":
    main()

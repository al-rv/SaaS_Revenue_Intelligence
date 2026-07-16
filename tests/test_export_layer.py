from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DASHBOARD_EXPORTS, PROCESSED_DATA_DIR


def test_dashboard_export_files_exist() -> None:
    for filename in DASHBOARD_EXPORTS:
        path = PROCESSED_DATA_DIR / filename
        assert path.exists(), f"Missing export file: {path}"


def test_dashboard_export_files_have_rows() -> None:
    for filename in DASHBOARD_EXPORTS:
        path = PROCESSED_DATA_DIR / filename
        df = pd.read_parquet(path)
        assert len(df) > 0, f"Export file is empty: {filename}"


def test_executive_monthly_has_expected_columns() -> None:
    path = PROCESSED_DATA_DIR / "executive_monthly.parquet"
    df = pd.read_parquet(path)
    expected = {
        "month_start",
        "total_mrr",
        "arr",
        "active_accounts",
        "logo_churn_rate",
        "net_revenue_retention",
        "arpu",
    }
    assert expected.issubset(set(df.columns))


def test_churn_drivers_export_matches_config_count() -> None:
    assert len(DASHBOARD_EXPORTS) == 5

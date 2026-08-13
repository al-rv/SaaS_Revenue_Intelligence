from __future__ import annotations

from pathlib import Path

import pytest

from src.config import DASHBOARD_EXPORTS, DEMO_DATA_DIR, PROCESSED_DATA_DIR
from src.dashboard import load_parquet, resolve_dashboard_export


def test_demo_exports_are_committed_for_deployment() -> None:
    for filename in DASHBOARD_EXPORTS:
        path = DEMO_DATA_DIR / filename
        assert path.exists(), f"Missing committed demo export: {path}"
        assert path.stat().st_size > 0


def test_resolve_prefers_processed_when_present() -> None:
    filename = "executive_monthly.parquet"
    processed = PROCESSED_DATA_DIR / filename
    if not processed.exists():
        pytest.skip("Local processed export not available")
    assert resolve_dashboard_export(filename) == processed


def test_resolve_falls_back_to_demo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    filename = "executive_monthly.parquet"
    empty_processed = tmp_path / "processed"
    empty_processed.mkdir()
    monkeypatch.setattr("src.dashboard.PROCESSED_DATA_DIR", empty_processed)

    resolved = resolve_dashboard_export(filename)
    assert resolved == DEMO_DATA_DIR / filename
    frame = load_parquet(filename)
    assert not frame.empty

"""DuckDB connection helpers"""

from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

from src.config import DUCKDB_PATH, PROCESSED_DATA_DIR, ensure_directories

def ensure_database_directoy() -> Path:
    """Ensure the processed data directory exists before opening DUckDB."""
    ensure_directories()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DUCKDB_PATH

@contextmanager
def get_connection(db_path: Path | None=None, read_only: bool=False) ->Iterator[duckdb.DuckDBPyConnection]:
    """Open a DuckDB connection and close it when finished"""
    db_path = db_path or ensure_database_directoy()
    connection = duckdb.connect(str(db_path), read_only=read_only)
    try:
        yield connection
    finally:
        connection.close()
        
def test_connection(db_path:Path|None=None) -> int:
    """Verify DuckDB can connect and run a simple query"""
    with get_connection(db_path=db_path) as connection:
        result = connection.execute("SELECT 1 AS ok").fetchone()
    if result is None or result[0] != 1:
        raise RuntimeError("DuckDB connection test failed.")
    return result[0]        
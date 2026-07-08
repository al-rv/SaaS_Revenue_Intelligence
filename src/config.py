"""Project paths and env config"""

from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv

# By convention, variables written in all uppercase letters (e.g., MAX_SPEED, PI) are treated as constants — values that should not change during program execution.
# Python doesn’t enforce immutability, but the uppercase signals to other developers: “Don’t modify this.”

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / 'data'))
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
SAMPLE_DATA_DIR = DATA_DIR / 'sample'
SQL_DIR = PROJECT_ROOT / 'sql'
DOCS_DIR = PROJECT_ROOT / 'docs'
ASSETS_DIR = PROJECT_ROOT / 'assets'

DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", PROCESSED_DATA_DIR / "saas_revenue_intelligence.duckdb"))
if not DUCKDB_PATH.is_absolute():
    DUCKDB_PATH = PROJECT_ROOT / DUCKDB_PATH

MIN_PYTHON_VERSION = (3, 11)

REQUIRED_DIRECTORIES = (
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    SAMPLE_DATA_DIR,
    SQL_DIR,
    DOCS_DIR,
    ASSETS_DIR,
)

RAW_TABLE_FILES = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subsciptions.csv",
    "feature_usage": "ravenstack_feature_usage.csv",
    "support_tickets": "ravenstacck_support_tickets.csv",
    "churn_events": "ravenstack_churn_events.csv"
}

REQUIRED_PACKAGES = (
    "pandas",
    "numpy",
    "duckdb",
    "streamlit",
    "plotly",
    "pyarrow",
    "dotenv",
    "pytest",
)

def ensure_directories() -> None:
    """Create expected project direcories if they not exist"""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
        
def raw_table_path(table_name: str) -> Path:
    """Return the expected on-disk path for a raw source table."""
    if table_name not in RAW_TABLE_FILES:
        raise KeyError(f'Unknown raw tables: {table_name}')
    return RAW_DATA_DIR/ RAW_TABLE_FILES[table_name]
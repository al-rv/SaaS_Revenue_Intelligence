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

KAGGLE_DATASET_SLUG = "rivalytics/saas-subscription-and-churn-analytics-dataset"
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
    "subscriptions": "ravenstack_subscriptions.csv",
    "feature_usage": "ravenstack_feature_usage.csv",
    "support_tickets": "ravenstack_support_tickets.csv",
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

DASHBOARD_EXPORTS: dict[str, str] = {
    "executive_monthly.parquet": "SELECT * FROM marts.mart_executive_monthly ORDER BY month_start",
    "mrr_movement_monthly.parquet": (
        "SELECT * FROM marts.fct_mrr_movement_monthly ORDER BY month_start"
    ),
    "cohort_retention.parquet": (
        "SELECT * FROM marts.fct_cohort_retention "
        "ORDER BY cohort_month, month_number"
    ),
    "churn_drivers.parquet": (
        "SELECT * FROM marts.mart_churn_drivers ORDER BY month_start, account_id"
    ),
    "support_usage_monthly.parquet": """
        SELECT
            COALESCE(s.account_id, u.account_id) AS account_id,
            COALESCE(s.month_start, u.month_start) AS month_start,
            COALESCE(s.ticket_count, 0) AS ticket_count,
            COALESCE(s.high_priority_ticket_count, 0) AS high_priority_ticket_count,
            COALESCE(s.escalated_ticket_count, 0) AS escalated_ticket_count,
            s.avg_resolution_hours,
            COALESCE(s.sla_breach_count, 0) AS sla_breach_count,
            s.avg_satisfaction_score,
            s.avg_first_response_minutes,
            COALESCE(u.usage_event_count, 0) AS usage_event_count,
            COALESCE(u.total_usage_count, 0) AS total_usage_count,
            COALESCE(u.active_feature_count, 0) AS active_feature_count,
            COALESCE(u.total_duration_minutes, 0) AS total_duration_minutes,
            COALESCE(u.error_count, 0) AS error_count,
            u.error_rate,
            COALESCE(u.beta_feature_event_count, 0) AS beta_feature_event_count
        FROM marts.fct_support_monthly AS s
        FULL OUTER JOIN marts.fct_usage_monthly AS u
            ON s.account_id = u.account_id
            AND s.month_start = u.month_start
        ORDER BY month_start, account_id
    """,
}

def ensure_directories() -> None:
    """Create expected project direcories if they not exist"""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
        
def raw_table_path(table_name: str) -> Path:
    """Return the expected on-disk path for a raw source table."""
    if table_name not in RAW_TABLE_FILES:
        raise KeyError(f'Unknown raw tables: {table_name}')
    return RAW_DATA_DIR/ RAW_TABLE_FILES[table_name]
from __future__ import annotations

from pathlib import Path

from src.config import DUCKDB_PATH
from src.db import get_connection


def _single_value(query: str) -> int:
    with get_connection(read_only=True) as conn:
        value = conn.execute(query).fetchone()
    assert value is not None
    return int(value[0])


def test_duckdb_file_exists() -> None:
    assert Path(DUCKDB_PATH).exists()


def test_staging_tables_exist() -> None:
    with get_connection(read_only=True) as conn:
        tables = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'staging'
            ORDER BY table_name
            """
        ).fetchall()
    table_names = {row[0] for row in tables}
    expected = {
        "stg_accounts",
        "stg_subscriptions",
        "stg_feature_usage",
        "stg_support_tickets",
        "stg_churn_events",
    }
    assert expected.issubset(table_names)


def test_primary_key_uniqueness() -> None:
    checks = {
        "staging.stg_accounts": "account_id",
        "staging.stg_subscriptions": "subscription_id",
        "staging.stg_feature_usage": "usage_id",
        "staging.stg_support_tickets": "ticket_id",
        "staging.stg_churn_events": "churn_event_id",
    }
    for table_name, key_col in checks.items():
        duplicates = _single_value(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {key_col}
                FROM {table_name}
                GROUP BY 1
                HAVING COUNT(*) > 1
            ) t
            """
        )
        assert duplicates == 0, f"Duplicate key values found in {table_name}.{key_col}"


def test_foreign_key_integrity() -> None:
    orphan_subscriptions = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_subscriptions s
        LEFT JOIN staging.stg_accounts a ON s.account_id = a.account_id
        WHERE a.account_id IS NULL
        """
    )
    orphan_tickets = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_support_tickets t
        LEFT JOIN staging.stg_accounts a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
        """
    )
    orphan_churn = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_churn_events c
        LEFT JOIN staging.stg_accounts a ON c.account_id = a.account_id
        WHERE a.account_id IS NULL
        """
    )
    orphan_usage = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_feature_usage f
        LEFT JOIN staging.stg_subscriptions s ON f.subscription_id = s.subscription_id
        WHERE s.subscription_id IS NULL
        """
    )
    assert orphan_subscriptions == 0
    assert orphan_tickets == 0
    assert orphan_churn == 0
    assert orphan_usage == 0


def test_no_negative_mrr() -> None:
    negatives = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_subscriptions
        WHERE mrr_amount < 0 OR arr_amount < 0
        """
    )
    assert negatives == 0


def test_required_dates_are_valid() -> None:
    invalid_signup_dates = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_accounts
        WHERE signup_date IS NULL
        """
    )
    invalid_start_dates = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_subscriptions
        WHERE start_date IS NULL
        """
    )
    invalid_usage_dates = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_feature_usage
        WHERE usage_date IS NULL
        """
    )
    invalid_churn_dates = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_churn_events
        WHERE churn_date IS NULL
        """
    )
    invalid_submitted_at = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_support_tickets
        WHERE submitted_at IS NULL
        """
    )
    assert invalid_signup_dates == 0
    assert invalid_start_dates == 0
    assert invalid_usage_dates == 0
    assert invalid_churn_dates == 0
    assert invalid_submitted_at == 0

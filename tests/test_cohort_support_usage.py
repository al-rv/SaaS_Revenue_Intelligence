from __future__ import annotations

from src.db import get_connection


def _single_value(query: str) -> float:
    with get_connection(read_only=True) as conn:
        value = conn.execute(query).fetchone()
    assert value is not None
    return float(value[0])


def test_phase7_mart_tables_exist() -> None:
    with get_connection(read_only=True) as conn:
        tables = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'marts'
            """
        ).fetchall()
    table_names = {row[0] for row in tables}
    expected = {
        "fct_cohort_retention",
        "fct_support_monthly",
        "fct_usage_monthly",
        "mart_churn_drivers",
    }
    assert expected.issubset(table_names)


def test_cohort_month_zero_retention_is_100_percent() -> None:
    invalid = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.fct_cohort_retention
        WHERE month_number = 0
          AND ABS(retention_rate - 1.0) > 0.0001
        """
    )
    assert invalid == 0


def test_support_monthly_does_not_duplicate_tickets() -> None:
    mismatched = _single_value(
        """
        SELECT COUNT(*)
        FROM (
            SELECT SUM(ticket_count) AS rolled_up_tickets
            FROM marts.fct_support_monthly
        ) rolled
        CROSS JOIN (
            SELECT COUNT(*) AS source_tickets
            FROM staging.stg_support_tickets
            WHERE submitted_at IS NOT NULL
        ) source
        WHERE rolled.rolled_up_tickets <> source.source_tickets
        """
    )
    assert mismatched == 0


def test_usage_monthly_does_not_duplicate_events() -> None:
    mismatched = _single_value(
        """
        SELECT COUNT(*)
        FROM (
            SELECT SUM(usage_event_count) AS rolled_up_events
            FROM marts.fct_usage_monthly
        ) rolled
        CROSS JOIN (
            SELECT COUNT(*) AS source_events
            FROM staging.stg_feature_usage
            WHERE usage_date IS NOT NULL
        ) source
        WHERE rolled.rolled_up_events <> source.source_events
        """
    )
    assert mismatched == 0


def test_churn_drivers_grain_is_unique() -> None:
    duplicates = _single_value(
        """
        SELECT COUNT(*)
        FROM (
            SELECT account_id, month_start
            FROM marts.mart_churn_drivers
            GROUP BY account_id, month_start
            HAVING COUNT(*) > 1
        ) d
        """
    )
    assert duplicates == 0


def test_churn_drivers_row_count_matches_spine() -> None:
    mismatched = _single_value(
        """
        SELECT COUNT(*)
        FROM (
            SELECT COUNT(*) AS spine_rows
            FROM intermediate.int_account_month_spine
        ) s
        CROSS JOIN (
            SELECT COUNT(*) AS driver_rows
            FROM marts.mart_churn_drivers
        ) d
        WHERE s.spine_rows <> d.driver_rows
        """
    )
    assert mismatched == 0

from __future__ import annotations

from src.db import get_connection


def _single_value(query: str) -> float:
    with get_connection(read_only=True) as conn:
        value = conn.execute(query).fetchone()
    assert value is not None
    return float(value[0])


def test_revenue_mart_tables_exist() -> None:
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
        "dim_account",
        "fct_account_monthly_mrr",
        "fct_mrr_movement_monthly",
        "mart_executive_monthly",
    }
    assert expected.issubset(table_names)


def test_mrr_is_never_negative() -> None:
    negatives = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.fct_account_monthly_mrr
        WHERE mrr < 0
           OR prior_mrr < 0
           OR new_mrr < 0
           OR reactivation_mrr < 0
           OR expansion_mrr < 0
           OR contraction_mrr < 0
           OR churned_mrr < 0
           OR retained_mrr < 0
        """
    )
    assert negatives == 0


def test_logo_churn_rate_between_zero_and_one() -> None:
    invalid_rates = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.mart_executive_monthly
        WHERE logo_churn_rate IS NOT NULL
          AND (logo_churn_rate < 0 OR logo_churn_rate > 1)
        """
    )
    assert invalid_rates == 0


def test_nrr_not_null_when_starting_mrr_exists() -> None:
    missing_nrr = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.mart_executive_monthly
        WHERE starting_mrr > 0
          AND net_revenue_retention IS NULL
        """
    )
    assert missing_nrr == 0


def test_company_mrr_equals_sum_of_account_mrr() -> None:
    mismatched_months = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.mart_executive_monthly e
        JOIN (
            SELECT
                month_start,
                SUM(mrr) AS account_mrr_sum
            FROM marts.fct_account_monthly_mrr
            GROUP BY month_start
        ) a
            ON e.month_start = a.month_start
        WHERE ABS(e.total_mrr - a.account_mrr_sum) > 0.01
        """
    )
    assert mismatched_months == 0


def test_movement_components_reconcile_to_ending_mrr() -> None:
    mismatched_months = _single_value(
        """
        SELECT COUNT(*)
        FROM marts.fct_mrr_movement_monthly
        WHERE ABS(
            starting_mrr
            + new_mrr
            + reactivation_mrr
            + expansion_mrr
            - contraction_mrr
            - churned_mrr
            - ending_mrr
        ) > 0.01
        """
    )
    assert mismatched_months == 0

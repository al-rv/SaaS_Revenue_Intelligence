from __future__ import annotations

from src.db import get_connection


def _single_value(query: str) -> int:
    with get_connection(read_only=True) as conn:
        value = conn.execute(query).fetchone()
    assert value is not None
    return int(value[0])


def test_account_month_spine_table_exists() -> None:
    with get_connection(read_only=True) as conn:
        tables = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'intermediate'
              AND table_name = 'int_account_month_spine'
            """
        ).fetchall()
    assert len(tables) == 1


def test_every_account_has_at_least_one_month() -> None:
    missing_accounts = _single_value(
        """
        SELECT COUNT(*)
        FROM staging.stg_accounts a
        LEFT JOIN (
            SELECT account_id
            FROM intermediate.int_account_month_spine
            GROUP BY account_id
        ) s ON a.account_id = s.account_id
        WHERE s.account_id IS NULL
        """
    )
    assert missing_accounts == 0


def test_no_account_month_before_signup() -> None:
    invalid_rows = _single_value(
        """
        SELECT COUNT(*)
        FROM intermediate.int_account_month_spine
        WHERE month_start < signup_month
        """
    )
    assert invalid_rows == 0


def test_account_month_grain_is_unique() -> None:
    duplicate_grain = _single_value(
        """
        SELECT COUNT(*)
        FROM (
            SELECT account_id, month_start
            FROM intermediate.int_account_month_spine
            GROUP BY account_id, month_start
            HAVING COUNT(*) > 1
        ) d
        """
    )
    assert duplicate_grain == 0


def test_months_since_signup_is_non_negative() -> None:
    negative_months = _single_value(
        """
        SELECT COUNT(*)
        FROM intermediate.int_account_month_spine
        WHERE months_since_signup < 0
        """
    )
    assert negative_months == 0


def test_account_age_matches_months_since_signup() -> None:
    mismatched_age = _single_value(
        """
        SELECT COUNT(*)
        FROM intermediate.int_account_month_spine
        WHERE account_age_months <> months_since_signup + 1
        """
    )
    assert mismatched_age == 0

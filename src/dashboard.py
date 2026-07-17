"""Shared data loading, filtering, and KPI logic for Streamlit pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DATA_DIR


@dataclass(frozen=True)
class DashboardFilters:
    start_date: date
    end_date: date
    plan_tiers: tuple[str, ...] = ()
    industries: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()


def load_parquet(filename: str) -> pd.DataFrame:
    """Load a dashboard export and normalize its date columns."""
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing dashboard export: {path}. Run `make build` first."
        )

    frame = pd.read_parquet(path)
    for column in ("month_start", "cohort_month", "signup_month"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def available_filter_values(frame: pd.DataFrame, column: str) -> list[str]:
    """Return sorted non-null values for a dashboard filter."""
    if column not in frame.columns:
        return []
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def apply_filters(
    frame: pd.DataFrame,
    filters: DashboardFilters,
) -> pd.DataFrame:
    """Apply date and account-dimension filters to account-month data."""
    filtered = frame.copy()
    start = pd.Timestamp(filters.start_date)
    end = pd.Timestamp(filters.end_date)
    filtered = filtered[
        filtered["month_start"].between(start, end, inclusive="both")
    ]

    selections = {
        "initial_plan_tier": filters.plan_tiers,
        "industry": filters.industries,
        "country": filters.countries,
    }
    for column, values in selections.items():
        if values and column in filtered.columns:
            filtered = filtered[filtered[column].isin(values)]
    return filtered


def aggregate_executive_monthly(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate filtered account-month facts into executive KPIs."""
    if frame.empty:
        return pd.DataFrame()

    grouped = (
        frame.groupby("month_start", as_index=False)
        .agg(
            total_mrr=("mrr", "sum"),
            active_accounts=("mrr", lambda values: int((values > 0).sum())),
            new_accounts=("new_mrr", lambda values: int((values > 0).sum())),
            churned_accounts=("churned_mrr", lambda values: int((values > 0).sum())),
            prior_active_accounts=(
                "prior_mrr",
                lambda values: int((values > 0).sum()),
            ),
            starting_mrr=("prior_mrr", "sum"),
            new_mrr=("new_mrr", "sum"),
            reactivation_mrr=("reactivation_mrr", "sum"),
            expansion_mrr=("expansion_mrr", "sum"),
            contraction_mrr=("contraction_mrr", "sum"),
            churned_mrr=("churned_mrr", "sum"),
        )
        .sort_values("month_start")
    )
    grouped["arr"] = grouped["total_mrr"] * 12
    grouped["logo_churn_rate"] = (
        grouped["churned_accounts"]
        .div(grouped["prior_active_accounts"].replace(0, pd.NA))
        .astype("Float64")
    )
    grouped["net_revenue_retention"] = (
        grouped["starting_mrr"]
        + grouped["expansion_mrr"]
        - grouped["contraction_mrr"]
        - grouped["churned_mrr"]
    ).div(grouped["starting_mrr"].replace(0, pd.NA))
    grouped["arpu"] = grouped["total_mrr"].div(
        grouped["active_accounts"].replace(0, pd.NA)
    )
    return grouped


def revenue_by_plan(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate MRR by month and initial plan tier."""
    if frame.empty:
        return pd.DataFrame()
    return (
        frame.groupby(["month_start", "initial_plan_tier"], as_index=False)["mrr"]
        .sum()
        .sort_values(["month_start", "initial_plan_tier"])
    )

def aggregate_cohort_retention(frame: pd.DataFrame) -> pd.DataFrame:
    """Build filtered cohort retention at cohort-month x month-number grain."""
    if frame.empty:
        return pd.DataFrame()

    cohort_sizes = (
        frame[["account_id", "signup_month"]]
        .drop_duplicates()
        .groupby("signup_month", as_index=False)
        .agg(cohort_size=("account_id", "nunique"))
        .rename(columns={"signup_month": "cohort_month"})
    )
    status = frame[
        ["account_id", "signup_month", "month_start", "months_since_signup", "mrr"]
    ].copy()
    status["is_retained"] = (status["months_since_signup"] == 0) | (status["mrr"] > 0)
    retention = (
        status.groupby(
            ["signup_month", "months_since_signup", "month_start"],
            as_index=False,
        )
        .agg(
            accounts_in_month=("account_id", "nunique"),
            retained_accounts=("is_retained", "sum"),
        )
        .rename(
            columns={
                "signup_month": "cohort_month",
                "months_since_signup": "month_number",
            }
        )
        .merge(cohort_sizes, on="cohort_month", how="left")
    )
    retention["retention_rate"] = retention["retained_accounts"].div(
        retention["cohort_size"].replace(0, pd.NA)
    )
    return retention.sort_values(["cohort_month", "month_number"])


def churn_rate_by_dimension(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Calculate next-month churn rate by account dimension."""
    if frame.empty or dimension not in frame.columns:
        return pd.DataFrame()
    eligible = frame[frame["mrr"] > 0].copy()
    return (
        eligible.groupby(dimension, as_index=False)
        .agg(
            account_months=("account_id", "size"),
            next_month_churns=("churns_next_month", "sum"),
            mrr=("mrr", "sum"),
        )
        .assign(
            churn_rate=lambda values: values["next_month_churns"].div(
                values["account_months"].replace(0, pd.NA)
            )
        )
        .sort_values("churn_rate", ascending=False)
    )


def at_risk_accounts(frame: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Score active accounts using recent behavioral and support warning signals."""
    if frame.empty:
        return pd.DataFrame()

    ordered = frame.sort_values(["account_id", "month_start"]).copy()
    ordered["prior_usage_count"] = ordered.groupby("account_id")[
        "total_usage_count"
    ].shift(1)
    ordered["usage_change"] = (
        ordered["total_usage_count"] - ordered["prior_usage_count"]
    ).div(ordered["prior_usage_count"].replace(0, pd.NA))

    latest_month = ordered["month_start"].max()
    latest = ordered[
        (ordered["month_start"] == latest_month) & (ordered["mrr"] > 0)
    ].copy()
    error_threshold = latest["error_rate"].median(skipna=True)
    if pd.isna(error_threshold):
        error_threshold = 0.0

    latest["risk_score"] = 0
    latest["risk_score"] += (latest["usage_change"] <= -0.30).astype(int) * 35
    latest["risk_score"] += (latest["sla_breach_count"] > 0).astype(int) * 25
    latest["risk_score"] += (latest["high_priority_ticket_count"] > 0).astype(int) * 20
    latest["risk_score"] += (
        latest["error_rate"].fillna(0) > float(error_threshold)
    ).astype(int) * 20
    latest["risk_level"] = pd.cut(
        latest["risk_score"],
        bins=[-1, 24, 49, 100],
        labels=["Low", "Medium", "High"],
    )
    columns = [
        "account_id",
        "initial_plan_tier",
        "industry",
        "mrr",
        "risk_score",
        "risk_level",
        "usage_change",
        "ticket_count",
        "sla_breach_count",
        "error_rate",
    ]
    return latest[columns].sort_values(
        ["risk_score", "mrr"],
        ascending=[False, False],
    ).head(limit)


def latest_kpis(executive: pd.DataFrame) -> dict[str, float | int | pd.Timestamp]:
    """Return the latest period's KPI values."""
    if executive.empty:
        return {}
    latest = executive.sort_values("month_start").iloc[-1]
    return {
        "month_start": latest["month_start"],
        "total_mrr": float(latest["total_mrr"]),
        "arr": float(latest["arr"]),
        "active_accounts": int(latest["active_accounts"]),
        "logo_churn_rate": (
            float(latest["logo_churn_rate"])
            if pd.notna(latest["logo_churn_rate"])
            else 0.0
        ),
        "net_revenue_retention": (
            float(latest["net_revenue_retention"])
            if pd.notna(latest["net_revenue_retention"])
            else 0.0
        ),
        "arpu": float(latest["arpu"]) if pd.notna(latest["arpu"]) else 0.0,
    }


def export_path(filename: str) -> Path:
    """Return the path to a dashboard export."""
    return PROCESSED_DATA_DIR / filename

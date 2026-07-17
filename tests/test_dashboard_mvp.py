from __future__ import annotations

from src.charts import line_chart, movement_trend, mrr_by_plan, mrr_waterfall
from src.dashboard import (
    DashboardFilters,
    aggregate_executive_monthly,
    apply_filters,
    latest_kpis,
    load_parquet,
    revenue_by_plan,
)


def test_dashboard_data_loads_and_aggregates() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    filters = DashboardFilters(
        start_date=drivers["month_start"].min().date(),
        end_date=drivers["month_start"].max().date(),
    )
    filtered = apply_filters(drivers, filters)
    executive = aggregate_executive_monthly(filtered)
    kpis = latest_kpis(executive)

    assert not filtered.empty
    assert not executive.empty
    assert float(kpis["total_mrr"]) >= 0
    assert int(kpis["active_accounts"]) >= 0


def test_dimension_filters_reduce_or_preserve_rows() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    plan = drivers["initial_plan_tier"].dropna().iloc[0]
    filters = DashboardFilters(
        start_date=drivers["month_start"].min().date(),
        end_date=drivers["month_start"].max().date(),
        plan_tiers=(str(plan),),
    )
    filtered = apply_filters(drivers, filters)

    assert len(filtered) <= len(drivers)
    assert set(filtered["initial_plan_tier"].dropna().unique()) == {plan}


def test_reusable_charts_return_figures() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    executive = aggregate_executive_monthly(drivers)
    plans = revenue_by_plan(drivers)
    latest = executive.iloc[-1]

    figures = [
        line_chart(executive, "total_mrr", "MRR", "MRR"),
        movement_trend(executive),
        mrr_waterfall(latest),
        mrr_by_plan(plans),
    ]
    assert all(len(figure.data) > 0 for figure in figures)

from __future__ import annotations

from src.charts import adoption_heatmap, bar_chart, cohort_heatmap, retention_curve
from src.dashboard import (
    aggregate_cohort_retention,
    at_risk_accounts,
    churn_rate_by_dimension,
    load_parquet,
)


def test_cohort_dashboard_models_and_charts() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    cohorts = aggregate_cohort_retention(drivers)
    sizes = cohorts[["cohort_month", "cohort_size"]].drop_duplicates()
    selected = cohorts[cohorts["cohort_month"] == cohorts["cohort_month"].max()]

    assert not cohorts.empty
    assert (cohorts.loc[cohorts["month_number"] == 0, "retention_rate"] == 1).all()
    assert len(cohort_heatmap(cohorts).data) > 0
    assert len(retention_curve(selected, "Selected cohort").data) > 0
    assert len(
        bar_chart(
            sizes,
            x="cohort_month",
            y="cohort_size",
            title="Cohort size",
        ).data
    ) > 0


def test_churn_driver_models() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    by_plan = churn_rate_by_dimension(drivers, "initial_plan_tier")
    risks = at_risk_accounts(drivers)

    assert "churn_reason_code" in drivers.columns
    assert by_plan["churn_rate"].between(0, 1).all()
    assert risks["risk_score"].between(0, 100).all()
    assert not risks.duplicated("account_id").any()


def test_feature_adoption_chart() -> None:
    drivers = load_parquet("churn_drivers.parquet")
    adoption = (
        drivers.groupby(["initial_plan_tier", "industry"], as_index=False)
        .agg(active_feature_count=("active_feature_count", "mean"))
    )

    assert len(adoption_heatmap(adoption).data) > 0

"""Churn-driver dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.charts import bar_chart
from src.dashboard import (
    apply_filters,
    at_risk_accounts,
    churn_rate_by_dimension,
    load_parquet,
)
from src.ui import configure_page, currency, render_sidebar_filters

configure_page("Churn Drivers", "⚠️")


@st.cache_data
def load_driver_data() -> pd.DataFrame:
    return load_parquet("churn_drivers.parquet")


st.title("Churn Drivers")
st.caption("Which customer segments and behavioral signals precede churn?")

try:
    drivers = load_driver_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

filters = render_sidebar_filters(drivers, key_prefix="churn")
filtered = apply_filters(drivers, filters)
if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

active = filtered[filtered["mrr"] > 0]
risks = at_risk_accounts(filtered, limit=10_000)
next_churns = int(active["churns_next_month"].sum())
at_risk_mrr = float(risks.loc[risks["risk_score"] >= 50, "mrr"].sum())

metrics = st.columns(3)
metrics[0].metric("Observed next-month churns", f"{next_churns:,}")
metrics[1].metric("High-risk accounts", f"{(risks['risk_score'] >= 50).sum():,}")
metrics[2].metric("High-risk MRR", currency(at_risk_mrr))

by_plan = churn_rate_by_dimension(filtered, "initial_plan_tier")
by_industry = churn_rate_by_dimension(filtered, "industry")
left, right = st.columns(2)
with left:
    st.plotly_chart(
        bar_chart(
            by_plan,
            x="initial_plan_tier",
            y="churn_rate",
            title="Next-month churn rate by plan",
            x_title="Initial plan tier",
            y_title="Churn rate",
            percent=True,
            color="#EF4444",
        ),
        width="stretch",
        theme=None,
    )
with right:
    st.plotly_chart(
        bar_chart(
            by_industry,
            x="industry",
            y="churn_rate",
            title="Next-month churn rate by industry",
            x_title="Industry",
            y_title="Churn rate",
            percent=True,
            color="#F59E0B",
        ),
        width="stretch",
        theme=None,
    )

reason_rows = filtered[
    filtered["is_churn_month"] & filtered["churn_reason_code"].notna()
]
reasons = (
    reason_rows.assign(
        churn_reason=lambda values: values["churn_reason_code"]
        .astype(str)
        .str.replace("_", " ")
        .str.title()
    )
    .groupby("churn_reason", as_index=False)
    .agg(churned_accounts=("account_id", "nunique"))
    .sort_values("churned_accounts", ascending=False)
)
pre_churn = (
    filtered[filtered["months_until_churn"].between(0, 6, inclusive="both")]
    .assign(months_before_churn=lambda values: -values["months_until_churn"])
    .groupby("months_before_churn", as_index=False)
    .agg(avg_usage_count=("total_usage_count", "mean"))
    .sort_values("months_before_churn")
)

left, right = st.columns(2)
with left:
    if reasons.empty:
        st.info("No coded churn reasons match the current filters.")
    else:
        st.plotly_chart(
            bar_chart(
                reasons,
                x="churn_reason",
                y="churned_accounts",
                title="Recorded churn reasons",
                x_title="Reason",
                y_title="Churned accounts",
                color="#64748B",
            ),
            width="stretch",
            theme=None,
        )
with right:
    st.plotly_chart(
        bar_chart(
            pre_churn,
            x="months_before_churn",
            y="avg_usage_count",
            title="Usage pattern before churn",
            x_title="Months before churn (0 = churn month)",
            y_title="Average usage count",
            color="#2563EB",
        ),
        width="stretch",
        theme=None,
    )

st.subheader("Accounts requiring customer-success review")
if risks.empty:
    st.info("No active accounts are available in the latest filtered month.")
else:
    display = risks.head(20).copy()
    display["usage_change"] = display["usage_change"].fillna(0) * 100
    display["error_rate"] = display["error_rate"].fillna(0)
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "mrr": st.column_config.NumberColumn("MRR", format="$%.0f"),
            "usage_change": st.column_config.NumberColumn(
                "Usage change",
                format="%.1f%%",
            ),
            "error_rate": st.column_config.NumberColumn(
                "Error rate",
                format="%.2f",
            ),
            "risk_score": st.column_config.ProgressColumn(
                "Risk score",
                min_value=0,
                max_value=100,
            ),
        },
    )

st.info(
    "**Recommended action:** Route high-risk, high-MRR accounts to customer "
    "success first. Investigate usage declines, unresolved priority tickets, "
    "and elevated errors before launching broad retention discounts."
)

with st.expander("Metric definitions and risk model"):
    st.markdown(
        """
        - **Next-month churn rate:** active account-months that churn in the next
          month divided by all active account-months.
        - **Usage before churn:** average product usage indexed relative to each
          account's churn month.
        - **Risk score:** 35 points for a 30%+ usage decline, 25 for an SLA
          breach, 20 for a high-priority ticket, and 20 for above-median errors.
        - This score is an explainable prioritization heuristic, not a causal or
          predictive machine-learning model.
        """
    )

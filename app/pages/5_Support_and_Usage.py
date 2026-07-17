"""Support and product-usage dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.charts import adoption_heatmap, bar_chart, line_chart
from src.dashboard import apply_filters, load_parquet
from src.ui import configure_page, render_sidebar_filters

configure_page("Support and Usage", "🛠️")


@st.cache_data
def load_driver_data() -> pd.DataFrame:
    return load_parquet("churn_drivers.parquet")


st.title("Support and Usage")
st.caption("How do service quality and product adoption relate to retention?")

try:
    drivers = load_driver_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

filters = render_sidebar_filters(drivers, key_prefix="support")
filtered = apply_filters(drivers, filters)
if filtered.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

monthly = (
    filtered.groupby("month_start", as_index=False)
    .agg(
        ticket_count=("ticket_count", "sum"),
        avg_resolution_hours=("avg_resolution_hours", "mean"),
        sla_breach_count=("sla_breach_count", "sum"),
        active_feature_count=("active_feature_count", "mean"),
        error_rate=("error_rate", "mean"),
        churns_next_month=("churns_next_month", "mean"),
    )
    .sort_values("month_start")
)
monthly["sla_breach_rate"] = monthly["sla_breach_count"].div(
    monthly["ticket_count"].replace(0, pd.NA)
)

top_metrics = st.columns(2)
top_metrics[0].metric("Support tickets", f"{monthly['ticket_count'].sum():,.0f}")
top_metrics[1].metric(
    "Avg. resolution time",
    f"{monthly['avg_resolution_hours'].mean():.1f} hrs",
)
overall_breach = monthly["sla_breach_count"].sum() / max(
    monthly["ticket_count"].sum(),
    1,
)
bottom_metrics = st.columns(2)
bottom_metrics[0].metric("SLA breach rate", f"{overall_breach:.1%}")
bottom_metrics[1].metric(
    "Avg. active features",
    f"{filtered['active_feature_count'].mean():.1f}",
)

left, right = st.columns(2)
with left:
    st.plotly_chart(
        line_chart(
            monthly,
            "ticket_count",
            "Support tickets by month",
            "Tickets",
            color="#2563EB",
        ),
        width="stretch",
        theme=None,
    )
with right:
    st.plotly_chart(
        line_chart(
            monthly,
            "avg_resolution_hours",
            "Average resolution time",
            "Hours",
            color="#F59E0B",
        ),
        width="stretch",
        theme=None,
    )

left, right = st.columns(2)
with left:
    st.plotly_chart(
        line_chart(
            monthly,
            "sla_breach_rate",
            "SLA breach rate",
            "Breach rate",
            percent=True,
            color="#EF4444",
        ),
        width="stretch",
        theme=None,
    )
with right:
    adoption = (
        filtered.groupby(["initial_plan_tier", "industry"], as_index=False)
        .agg(active_feature_count=("active_feature_count", "mean"))
    )
    st.plotly_chart(
        adoption_heatmap(adoption),
        width="stretch",
        theme=None,
    )

error_sample = filtered[
    filtered["error_rate"].notna() & (filtered["mrr"] > 0)
].copy()
if not error_sample.empty:
    try:
        error_sample["error_band"] = pd.qcut(
            error_sample["error_rate"],
            q=4,
            labels=["Low", "Moderate", "High", "Very high"],
            duplicates="drop",
        )
    except ValueError:
        error_sample["error_band"] = "All observed"
    error_churn = (
        error_sample.groupby("error_band", observed=True, as_index=False)
        .agg(
            next_month_churn_rate=("churns_next_month", "mean"),
            account_months=("account_id", "size"),
        )
    )
    st.plotly_chart(
        bar_chart(
            error_churn,
            x="error_band",
            y="next_month_churn_rate",
            title="Next-month churn rate by product error band",
            x_title="Error-rate band",
            y_title="Next-month churn rate",
            percent=True,
            color="#7C3AED",
        ),
        width="stretch",
        theme=None,
    )

worst_resolution = monthly.loc[monthly["avg_resolution_hours"].idxmax()]
st.info(
    f"**Service signal:** Resolution time peaked in "
    f"**{pd.Timestamp(worst_resolution['month_start']):%b %Y}** at "
    f"**{float(worst_resolution['avg_resolution_hours']):.1f} hours**. "
    "Review support capacity and escalation causes for that period, then target "
    "adoption coaching toward low-feature-use segments."
)

with st.expander("Metric definitions"):
    st.markdown(
        """
        - **Resolution time:** average hours from ticket submission to resolution.
        - **SLA breach rate:** tickets taking more than 48 hours divided by all tickets.
        - **Active features:** distinct product features used per account-month.
        - **Error rate:** recorded feature errors divided by product usage count.
        - **Next-month churn rate:** share of active account-months followed by churn.
        """
    )

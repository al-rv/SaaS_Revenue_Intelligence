"""Revenue intelligence dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.charts import line_chart, movement_trend, mrr_by_plan, mrr_waterfall
from src.dashboard import (
    aggregate_executive_monthly,
    apply_filters,
    load_parquet,
    revenue_by_plan,
)
from src.ui import configure_page, currency, render_sidebar_filters

configure_page("Revenue Intelligence", "💰")


@st.cache_data
def load_driver_data() -> pd.DataFrame:
    return load_parquet("churn_drivers.parquet")


st.title("Revenue Intelligence")
st.caption("MRR movement, plan contribution, and monetization efficiency")

try:
    drivers = load_driver_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

filters = render_sidebar_filters(drivers, key_prefix="revenue")
filtered = apply_filters(drivers, filters)
executive = aggregate_executive_monthly(filtered)

if executive.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

latest = executive.sort_values("month_start").iloc[-1]
latest_month = pd.Timestamp(latest["month_start"])

top_summary = st.columns(3)
top_summary[0].metric("Ending MRR", currency(float(latest["total_mrr"])))
top_summary[1].metric("New MRR", currency(float(latest["new_mrr"])))
top_summary[2].metric("Expansion", currency(float(latest["expansion_mrr"])))

bottom_summary = st.columns(2)
bottom_summary[0].metric("Contraction", currency(float(latest["contraction_mrr"])))
bottom_summary[1].metric("Churned MRR", currency(float(latest["churned_mrr"])))

left, right = st.columns([1, 1])
with left:
    st.plotly_chart(mrr_waterfall(latest), width="stretch", theme=None)
with right:
    st.plotly_chart(movement_trend(executive), width="stretch", theme=None)

plan_monthly = revenue_by_plan(filtered)
left, right = st.columns([1.35, 1])
with left:
    st.plotly_chart(mrr_by_plan(plan_monthly), width="stretch", theme=None)
with right:
    st.plotly_chart(
        line_chart(
            executive,
            "arpu",
            "Average revenue per active account",
            "ARPU",
            color="#F59E0B",
        ),
        width="stretch",
        theme=None,
    )

movement_total = (
    float(latest["new_mrr"])
    + float(latest["reactivation_mrr"])
    + float(latest["expansion_mrr"])
    - float(latest["contraction_mrr"])
    - float(latest["churned_mrr"])
)
driver = "expansion" if latest["expansion_mrr"] >= latest["new_mrr"] else "new revenue"
st.info(
    f"**Revenue signal ({latest_month:%b %Y}):** Net modeled MRR movement was "
    f"{currency(movement_total)}. The larger positive contributor was **{driver}**."
)

with st.expander("Movement definitions"):
    st.markdown(
        """
        - **New MRR:** first positive recurring revenue for an account.
        - **Expansion:** increase from an already active account.
        - **Contraction:** decrease while the account remains active.
        - **Churned MRR:** prior MRR lost when account MRR falls to zero.
        """
    )

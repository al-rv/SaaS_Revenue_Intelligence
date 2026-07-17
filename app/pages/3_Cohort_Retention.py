"""Cohort retention dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.charts import bar_chart, cohort_heatmap, retention_curve
from src.dashboard import aggregate_cohort_retention, apply_filters, load_parquet
from src.ui import configure_page, render_sidebar_filters

configure_page("Cohort Retention", "🧭")


@st.cache_data
def load_driver_data() -> pd.DataFrame:
    return load_parquet("churn_drivers.parquet")


st.title("Cohort Retention")
st.caption("Do newer signup cohorts retain better than earlier cohorts?")

try:
    drivers = load_driver_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

filters = render_sidebar_filters(drivers, key_prefix="cohort")
filtered = apply_filters(drivers, filters)
cohorts = aggregate_cohort_retention(filtered)

if cohorts.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

cohort_sizes = (
    cohorts[["cohort_month", "cohort_size"]]
    .drop_duplicates()
    .sort_values("cohort_month")
)
month_three = cohorts[cohorts["month_number"] == 3]
weighted_m3 = (
    month_three["retained_accounts"].sum() / month_three["cohort_size"].sum()
    if not month_three.empty and month_three["cohort_size"].sum() > 0
    else 0.0
)

metrics = st.columns(3)
metrics[0].metric("Signup cohorts", f"{cohorts['cohort_month'].nunique():,}")
metrics[1].metric("Accounts analyzed", f"{cohort_sizes['cohort_size'].sum():,}")
metrics[2].metric("Weighted month-3 retention", f"{weighted_m3:.1%}")

st.plotly_chart(cohort_heatmap(cohorts), width="stretch", theme=None)

left, right = st.columns([1, 1.25])
with left:
    st.plotly_chart(
        bar_chart(
            cohort_sizes,
            x="cohort_month",
            y="cohort_size",
            title="Cohort size by signup month",
            y_title="Accounts",
        ),
        width="stretch",
        theme=None,
    )
with right:
    cohort_options = sorted(cohorts["cohort_month"].dropna().unique(), reverse=True)
    selected = st.selectbox(
        "Inspect signup cohort",
        cohort_options,
        format_func=lambda value: pd.Timestamp(value).strftime("%B %Y"),
    )
    selected_curve = cohorts[cohorts["cohort_month"] == selected]
    st.plotly_chart(
        retention_curve(
            selected_curve,
            pd.Timestamp(selected).strftime("%b %Y"),
        ),
        width="stretch",
        theme=None,
    )

best_m3 = month_three.sort_values("retention_rate", ascending=False).head(1)
if not best_m3.empty:
    best = best_m3.iloc[0]
    st.info(
        f"**Retention signal:** The strongest observed month-3 cohort is "
        f"**{pd.Timestamp(best['cohort_month']):%b %Y}** at "
        f"**{float(best['retention_rate']):.1%}**. Compare its onboarding and "
        "early product-adoption path with weaker cohorts."
    )

with st.expander("Metric definitions"):
    st.markdown(
        """
        - **Cohort:** accounts grouped by signup month.
        - **Month number:** completed calendar months since signup.
        - **Retention:** share of the original cohort with positive MRR in that month.
        - **Month 0:** 100% by definition because it is the acquisition month.
        """
    )

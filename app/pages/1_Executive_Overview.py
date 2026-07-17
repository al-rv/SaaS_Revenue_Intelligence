"""Executive overview dashboard page."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.charts import line_chart
from src.dashboard import (
    aggregate_executive_monthly,
    apply_filters,
    latest_kpis,
    load_parquet,
)
from src.ui import configure_page, currency, render_sidebar_filters

configure_page("Executive Overview", "📈")


@st.cache_data
def load_driver_data() -> pd.DataFrame:
    return load_parquet("churn_drivers.parquet")


st.title("Executive Overview")
st.caption("Recurring revenue health, customer momentum, and churn exposure")

try:
    drivers = load_driver_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

filters = render_sidebar_filters(drivers, key_prefix="executive")
filtered = apply_filters(drivers, filters)
executive = aggregate_executive_monthly(filtered)

if executive.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

kpis = latest_kpis(executive)
latest_month = pd.Timestamp(kpis["month_start"])
st.caption(f"Latest selected reporting month: {latest_month:%B %Y}")

top_metrics = st.columns(3)
top_metrics[0].metric("MRR", currency(float(kpis["total_mrr"])))
top_metrics[1].metric("ARR", currency(float(kpis["arr"])))
top_metrics[2].metric("Active accounts", f"{int(kpis['active_accounts']):,}")

bottom_metrics = st.columns(3)
bottom_metrics[0].metric("Logo churn", f"{float(kpis['logo_churn_rate']):.1%}")
bottom_metrics[1].metric("NRR", f"{float(kpis['net_revenue_retention']):.1%}")
bottom_metrics[2].metric("ARPU", currency(float(kpis["arpu"])))

left, right = st.columns(2)
with left:
    st.plotly_chart(
        line_chart(executive, "total_mrr", "MRR trend", "MRR"),
        width="stretch",
        theme=None,
    )
    st.plotly_chart(
        line_chart(
            executive,
            "logo_churn_rate",
            "Logo churn trend",
            "Logo churn",
            percent=True,
            color="#EF4444",
        ),
        width="stretch",
        theme=None,
    )
with right:
    st.plotly_chart(
        line_chart(
            executive,
            "active_accounts",
            "Active account trend",
            "Accounts",
            color="#06B6D4",
        ),
        width="stretch",
        theme=None,
    )
    st.plotly_chart(
        line_chart(
            executive,
            "net_revenue_retention",
            "Net revenue retention",
            "NRR",
            percent=True,
            color="#10B981",
        ),
        width="stretch",
        theme=None,
    )

peak_churn = executive.loc[executive["logo_churn_rate"].fillna(0).idxmax()]
growth = executive["total_mrr"].pct_change().iloc[-1]
if pd.isna(growth):
    growth = 0.0
peak_churn_rate = (
    float(peak_churn["logo_churn_rate"])
    if pd.notna(peak_churn["logo_churn_rate"])
    else 0.0
)

st.info(
    f"**Executive signal:** MRR changed {growth:+.1%} in the latest month. "
    f"Peak logo churn in the selected period was "
    f"{peak_churn_rate:.1%} "
    f"in {pd.Timestamp(peak_churn['month_start']):%b %Y}."
)

with st.expander("Metric definitions"):
    st.markdown(
        """
        - **MRR:** active subscription monthly recurring revenue.
        - **Logo churn:** churned accounts divided by prior active accounts.
        - **NRR:** starting MRR plus expansion, less contraction and churn,
          divided by starting MRR.
        - **ARPU:** total MRR divided by active accounts.
        """
    )

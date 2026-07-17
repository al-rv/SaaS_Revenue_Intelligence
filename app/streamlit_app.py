"""Home page for the SaaS Revenue Intelligence dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.dashboard import load_parquet
from src.ui import configure_page

configure_page("Home", "💼")

st.title("SaaS Revenue Intelligence")
st.caption("Production-style subscription analytics for growth and retention teams")

try:
    executive = load_parquet("executive_monthly.parquet")
    drivers = load_parquet("churn_drivers.parquet")
except FileNotFoundError as exc:
    st.error(str(exc))
    st.code("make build", language="bash")
    st.stop()

latest_month = executive["month_start"].max()

st.markdown(
    """
    This analytics product converts five relational SaaS datasets into a trusted
    monthly reporting layer. Use the pages below to inspect executive health,
    recurring-revenue movements, retention, churn risk, and customer experience.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("Data through", latest_month.strftime("%b %Y"))
col2.metric("Account-month records", f"{len(drivers):,}")
col3.metric("Reporting months", f"{executive['month_start'].nunique():,}")

st.subheader("Explore")
pages = [
    (        
        "Executive Overview",
        "MRR, ARR, active accounts, churn, NRR, and time-series health.",
        "pages/1_Executive_Overview.py",
        "📈",
    ),
    (
        "Revenue Intelligence",
        "MRR waterfall, movement mix, plan contribution, and ARPU.",
        "pages/2_Revenue_Intelligence.py",
        "💰",
    ),
    (
        "Cohort Retention",
        "Cohort heatmap, signup volume, and retention curves.",
        "pages/3_Cohort_Retention.py",
        "🧭",
    ),
    (
        "Churn Drivers",
        "Segment churn, churn reasons, warning signals, and at-risk accounts.",
        "pages/4_Churn_Drivers.py",
        "⚠️",
    ),
    (
        "Support and Usage",
        "Service quality, feature adoption, product errors, and churn.",
        "pages/5_Support_and_Usage.py",
        "🛠️",
    ),
]
for row_start in range(0, len(pages), 2):
    columns = st.columns(2)
    for column, (title, description, path, icon) in zip(
        columns,
        pages[row_start : row_start + 2],
    ):
        with column:
            st.markdown(f"### {title}")
            st.write(description)
            st.page_link(path, label=f"Open {title}", icon=icon)

with st.expander("Data and metric notes"):
    st.markdown(
        """
        - Raw data: Rivalytics / RavenStack synthetic SaaS dataset.
        - Dashboard source: precomputed Parquet exports from DuckDB marts.
        - MRR and churn definitions are documented in `docs/metric_definitions.md`.
        """
    )

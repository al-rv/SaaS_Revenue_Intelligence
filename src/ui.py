"""Shared Streamlit UI helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.dashboard import DashboardFilters, available_filter_values


def configure_page(title: str, icon: str = "📊") -> None:
    st.set_page_config(
        page_title=f"{title} | SaaS Revenue Intelligence",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {color-scheme: light;}
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 220px);
            color: #0F172A !important;
        }
        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.95) !important;
        }
        .block-container {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {
            color: #0F172A !important;
        }
        [data-testid="stMetricValue"] > div {
            font-size: clamp(1.75rem, 2.6vw, 2.35rem) !important;
            line-height: 1.15 !important;
        }
        [data-testid="stSidebar"] {
            background: #EAF0F8 !important;
            border-right: 1px solid #CBD5E1;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #0F172A !important;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 3px 8px;
            padding: 8px 10px;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: #DBEAFE;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #BFDBFE;
            color: #1D4ED8 !important;
            font-weight: 700;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNav"] a[aria-current="page"] p {
            color: #1D4ED8 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="input"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            border-color: #94A3B8 !important;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [role="combobox"],
        [data-testid="stSidebar"] [role="combobox"] * {
            color: #0F172A !important;
        }
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label {
            color: #0F172A !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters(
    frame: pd.DataFrame,
    *,
    key_prefix: str,
) -> DashboardFilters:
    """Render consistent account-month filters in the sidebar."""
    minimum = frame["month_start"].min().date()
    maximum = frame["month_start"].max().date()

    st.sidebar.header("Filters")
    date_range = st.sidebar.date_input(
        "Reporting period",
        value=(minimum, maximum),
        min_value=minimum,
        max_value=maximum,
        key=f"{key_prefix}_dates",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = minimum, maximum

    plans = st.sidebar.multiselect(
        "Initial plan tier",
        available_filter_values(frame, "initial_plan_tier"),
        key=f"{key_prefix}_plans",
        help="Leave empty to include every plan.",
    )
    industries = st.sidebar.multiselect(
        "Industry",
        available_filter_values(frame, "industry"),
        key=f"{key_prefix}_industries",
        help="Leave empty to include every industry.",
    )
    countries = st.sidebar.multiselect(
        "Country",
        available_filter_values(frame, "country"),
        key=f"{key_prefix}_countries",
        help="Leave empty to include every country.",
    )

    st.sidebar.caption("Empty selections include all values.")
    return DashboardFilters(
        start_date=start_date,
        end_date=end_date,
        plan_tiers=tuple(plans),
        industries=tuple(industries),
        countries=tuple(countries),
    )


def currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"

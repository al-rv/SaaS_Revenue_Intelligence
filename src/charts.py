"""Reusable Plotly charts for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

NAVY = "#0F172A"
BLUE = "#2563EB"
CYAN = "#06B6D4"
GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
SLATE = "#64748B"


def _apply_layout(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        title=title,
        title_font=dict(size=18, color=NAVY),
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            size=13,
            color=NAVY,
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=60, r=24, t=60, b=55),
        hovermode="x unified",
        legend_title_text="",
        legend=dict(
            font=dict(color=NAVY, size=12),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E2E8F0",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#CBD5E1",
            font=dict(color=NAVY),
        ),
    )
    figure.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#CBD5E1",
        tickfont=dict(color=NAVY, size=12),
        title_font=dict(color=NAVY, size=13),
        tickcolor="#64748B",
        automargin=True,
    )
    figure.update_yaxes(
        gridcolor="#E2E8F0",
        showline=True,
        linecolor="#CBD5E1",
        tickfont=dict(color=NAVY, size=12),
        title_font=dict(color=NAVY, size=13),
        tickcolor="#64748B",
        automargin=True,
        zerolinecolor="#94A3B8",
    )
    return figure


def line_chart(
    frame: pd.DataFrame,
    y: str,
    title: str,
    y_title: str,
    *,
    percent: bool = False,
    color: str = BLUE,
) -> go.Figure:
    figure = px.line(
        frame,
        x="month_start",
        y=y,
        markers=True,
        color_discrete_sequence=[color],
    )
    figure.update_traces(line=dict(width=3))
    figure.update_yaxes(title=y_title, tickformat=".1%" if percent else ",.0f")
    figure.update_xaxes(title=None)
    return _apply_layout(figure, title)


def movement_trend(frame: pd.DataFrame) -> go.Figure:
    columns = [
        "new_mrr",
        "reactivation_mrr",
        "expansion_mrr",
        "contraction_mrr",
        "churned_mrr",
    ]
    melted = frame.melt(
        id_vars="month_start",
        value_vars=columns,
        var_name="movement",
        value_name="mrr",
    )
    labels = {
        "new_mrr": "New",
        "reactivation_mrr": "Reactivation",
        "expansion_mrr": "Expansion",
        "contraction_mrr": "Contraction",
        "churned_mrr": "Churned",
    }
    melted["movement"] = melted["movement"].map(labels)
    figure = px.bar(
        melted,
        x="month_start",
        y="mrr",
        color="movement",
        barmode="group",
        color_discrete_map={
            "New": BLUE,
            "Reactivation": CYAN,
            "Expansion": GREEN,
            "Contraction": AMBER,
            "Churned": RED,
        },
    )
    figure.update_yaxes(title="MRR", tickformat=",.0f")
    figure.update_xaxes(title=None)
    return _apply_layout(figure, "Monthly MRR movements")


def mrr_waterfall(latest: pd.Series) -> go.Figure:
    starting = float(latest["starting_mrr"])
    ending = float(latest["total_mrr"])
    figure = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=[
                "absolute",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            x=[
                "Starting",
                "New",
                "Reactivation",
                "Expansion",
                "Contraction",
                "Churned",
                "Ending",
            ],
            y=[
                starting,
                float(latest["new_mrr"]),
                float(latest["reactivation_mrr"]),
                float(latest["expansion_mrr"]),
                -float(latest["contraction_mrr"]),
                -float(latest["churned_mrr"]),
                ending,
            ],
            increasing={"marker": {"color": GREEN}},
            decreasing={"marker": {"color": RED}},
            totals={"marker": {"color": BLUE}},
            connector={"line": {"color": SLATE}},
        )
    )
    figure.update_yaxes(title="MRR", tickformat=",.0f")
    return _apply_layout(
        figure,
        f"MRR waterfall — {pd.Timestamp(latest['month_start']):%b %Y}",
    )


def mrr_by_plan(frame: pd.DataFrame) -> go.Figure:
    figure = px.area(
        frame,
        x="month_start",
        y="mrr",
        color="initial_plan_tier",
        color_discrete_sequence=[BLUE, CYAN, GREEN, AMBER],
    )
    figure.update_yaxes(title="MRR", tickformat=",.0f")
    figure.update_xaxes(title=None)
    return _apply_layout(figure, "MRR by initial plan tier")

def cohort_heatmap(frame: pd.DataFrame) -> go.Figure:
    pivot = frame.pivot(
        index="cohort_month",
        columns="month_number",
        values="retention_rate",
    ).sort_index(ascending=False)
    labels = [pd.Timestamp(value).strftime("%b %Y") for value in pivot.index]
    figure = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=labels,
            colorscale=[
                [0.0, "#EFF6FF"],
                [0.5, "#60A5FA"],
                [1.0, "#1D4ED8"],
            ],
            zmin=0,
            zmax=1,
            colorbar=dict(title="Retention", tickformat=".0%"),
            hovertemplate=(
                "Cohort %{y}<br>Month %{x}<br>Retention %{z:.1%}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title="Months since signup", dtick=1)
    figure.update_yaxes(title="Signup cohort")
    return _apply_layout(figure, "Cohort retention heatmap")


def bar_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str | None = None,
    y_title: str | None = None,
    percent: bool = False,
    color: str = BLUE,
) -> go.Figure:
    figure = px.bar(frame, x=x, y=y, color_discrete_sequence=[color])
    figure.update_xaxes(title=x_title)
    figure.update_yaxes(
        title=y_title,
        tickformat=".1%" if percent else ",.0f",
    )
    return _apply_layout(figure, title)


def retention_curve(frame: pd.DataFrame, cohort_label: str) -> go.Figure:
    figure = px.line(
        frame,
        x="month_number",
        y="retention_rate",
        markers=True,
        color_discrete_sequence=[BLUE],
    )
    figure.update_traces(line=dict(width=3))
    figure.update_xaxes(title="Months since signup", dtick=1)
    figure.update_yaxes(title="Retention", tickformat=".0%", range=[0, 1.05])
    return _apply_layout(figure, f"Retention curve — {cohort_label}")


def adoption_heatmap(frame: pd.DataFrame) -> go.Figure:
    pivot = frame.pivot(
        index="initial_plan_tier",
        columns="industry",
        values="active_feature_count",
    )
    figure = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            colorbar=dict(title="Avg. features"),
            hovertemplate=(
                "Plan %{y}<br>Industry %{x}<br>Avg. features %{z:.1f}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title="Industry")
    figure.update_yaxes(title="Plan tier")
    return _apply_layout(figure, "Feature adoption matrix")


def scatter_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str,
    x_title: str,
    y_title: str,
    color: str | None = None,
) -> go.Figure:
    figure = px.scatter(
        frame,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=[BLUE, RED, GREEN, AMBER],
        opacity=0.7,
    )
    figure.update_xaxes(title=x_title)
    figure.update_yaxes(title=y_title)
    return _apply_layout(figure, title)


# =================================== CHARTS ================================= #

"""
Reusable Plotly chart builders for the Fitness Tracker dashboard.

All chart functions return a ``plotly.graph_objects.Figure``.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import CARDIO_METRIC_MAP

# ========================= Shared Style Constants ========================== #

_FONT = dict(family="Calibri", size=16, color="black")
_TITLE_FONT = dict(size=21, family="Calibri", color="black")


# ============================== Line Chart ================================= #


def make_line_chart(
    df_cat: pd.DataFrame, title: str, exercise_col: str
) -> go.Figure:
    """Build a line-and-marker chart for a single muscle group.

    Cardio exercises are handled specially — each exercise uses its own metric
    (Distance or Floors) rather than Weight.
    """
    fig = go.Figure()

    if df_cat.empty:
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20))
        )
        return fig

    if exercise_col == "Cardio Exercise":
        for exercise_name, sub in df_cat.groupby(exercise_col):
            metric_col, unit = CARDIO_METRIC_MAP.get(
                exercise_name, ("Distance", "Value")
            )
            sub_sorted = sub.sort_values("Date")
            if metric_col in sub_sorted:
                # Build customdata with Time and Calories when available
                extra_cols = [c for c in ["Time", "Calories"] if c in sub_sorted.columns]
                customdata = sub_sorted[extra_cols].values if extra_cols else None
                extra_hover = "".join(
                    f"<br>{c}: <b>%{{customdata[{i}]}}</b>"
                    for i, c in enumerate(extra_cols)
                )
                fig.add_trace(
                    go.Scatter(
                        x=sub_sorted["Date"],
                        y=sub_sorted[metric_col],
                        mode="lines+markers",
                        name=f"{exercise_name} ({unit})",
                        customdata=customdata,
                        hovertemplate=(
                            f"Exercise: <b>%{{fullData.name}}</b><br>"
                            f"Date: <b>%{{x|%m/%d/%Y}}</b><br>"
                            f"{unit}: <b>%{{y}}</b>"
                            f"{extra_hover}"
                            f"<extra></extra>"
                        ),
                    )
                )
        yaxis_title = "Miles / Floors"
    else:
        for exercise_name, sub in df_cat.groupby(exercise_col):
            sub_sorted = sub.sort_values("Date")
            set_cols = [
                c
                for c in ["Set 1", "Set 2", "Set 3", "Set 4", "Set 5"]
                if c in sub_sorted.columns
            ]
            set_template = "".join(
                f"<br>{c}: <b>%{{customdata[{i}]}}</b>"
                for i, c in enumerate(set_cols)
            )
            hovertemplate = (
                f"Exercise: <b>%{{fullData.name}}</b>"
                f"<br>Date: <b>%{{x|%m/%d/%Y}}</b>"
                f"<br>Weight: <b>%{{y}} lbs.</b>"
                f"{set_template}"
                "<extra></extra>"
            )
            customdata = sub_sorted[set_cols].values if set_cols else None
            fig.add_trace(
                go.Scatter(
                    x=sub_sorted["Date"],
                    y=sub_sorted["Weight"],
                    mode="lines+markers",
                    name=str(exercise_name),
                    hovertemplate=hovertemplate,
                    customdata=customdata,
                )
            )
        yaxis_title = "Weight (lbs)"

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20)),
        xaxis=dict(tickformat="%m/%d/%Y", title="Date"),
        yaxis=dict(title=yaxis_title),
        hovermode="closest",
        font=dict(size=12),
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    )

    return fig


# ============================== Bar Chart ================================== #


def make_bar_chart(
    df_counts: pd.DataFrame, exercise_col: str, title: str
) -> go.Figure:
    """Build a horizontal bar chart for exercise frequency.

    Args:
        df_counts: Two-column DataFrame with ``exercise_col`` and ``'Count'``.
        exercise_col: Column name that holds exercise names.
        title: Chart title.
    """
    fig = px.bar(
        df_counts,
        y=exercise_col,
        x="Count",
        color=exercise_col,
        text="Count",
        orientation="h",
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font=_TITLE_FONT),
        font=_FONT,
        yaxis=dict(tickfont=dict(size=16), title=dict(text=exercise_col, font=dict(size=16))),
        xaxis=dict(title=dict(text="Count", font=dict(size=16))),
        legend=dict(visible=False),
        hovermode="closest",
        bargap=0.08,
        bargroupgap=0,
    )
    fig.update_traces(
        textposition="auto",
        hovertemplate=f"<b>{exercise_col}:</b> %{{y}}<br><b>Count</b>: %{{x}}<extra></extra>",
    )
    return fig


# ============================== Pie Chart ================================== #


def make_pie_chart(
    df_counts: pd.DataFrame, exercise_col: str, title: str
) -> go.Figure:
    """Build a pie chart for exercise distribution.

    Args:
        df_counts: Two-column DataFrame with ``exercise_col`` and ``'Count'``.
        exercise_col: Column name that holds exercise names.
        title: Chart title.
    """
    fig = px.pie(df_counts, names=exercise_col, values="Count")
    fig.update_layout(
        title=dict(text=title, x=0.5, font=_TITLE_FONT),
        font=_FONT,
    )
    fig.update_traces(
        rotation=100,
        texttemplate="%{percent:.1%}",
        hovertemplate=f"<b>{exercise_col}:</b> %{{label}}<br><b>Count</b>: %{{value}}<extra></extra>",
    )
    return fig


# ========================= Empty Placeholder =============================== #

def empty_figure(text: str = "Please Select a Year") -> go.Figure:
    """Return an empty figure with a centered title placeholder."""
    fig = go.Figure()
    fig.update_layout(title=dict(text=text, x=0.5, font=dict(size=20)))
    return fig

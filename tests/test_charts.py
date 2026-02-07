# ============================== TEST CHARTS ================================= #

"""
Unit tests for ``src.visuals.charts``.
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.visuals.charts import (
    make_line_chart,
    make_bar_chart,
    make_pie_chart,
    empty_figure,
)


# ------------------------------ Fixtures ------------------------------------ #


@pytest.fixture
def push_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-01-01", "2026-01-03", "2026-01-05"]),
            "Push Exercise": ["Bench Press", "Incline DB", "Bench Press"],
            "Weight": [185, 50, 195],
            "Set 1": [10, 12, 8],
            "Set 2": [8, 10, 6],
            "Set 3": [6, 8, 5],
            "Set 4": ["", "", ""],
            "Set 5": ["", "", ""],
        }
    )


@pytest.fixture
def counts_df() -> pd.DataFrame:
    return pd.DataFrame(
        {"Push Exercise": ["Bench Press", "Incline DB"], "Count": [2, 1]}
    )


# -------------------------------- Tests ------------------------------------- #


class TestMakeLineChart:
    def test_returns_figure(self, push_df):
        fig = make_line_chart(push_df, "Test", "Push Exercise")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_empty_df_returns_figure(self):
        fig = make_line_chart(pd.DataFrame(), "Empty", "Push Exercise")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0


class TestMakeBarChart:
    def test_returns_figure(self, counts_df):
        fig = make_bar_chart(counts_df, "Push Exercise", "Test Bar")
        assert isinstance(fig, go.Figure)


class TestMakePieChart:
    def test_returns_figure(self, counts_df):
        fig = make_pie_chart(counts_df, "Push Exercise", "Test Pie")
        assert isinstance(fig, go.Figure)


class TestEmptyFigure:
    def test_default_text(self):
        fig = empty_figure()
        assert fig.layout.title.text == "Please Select a Year"

    def test_custom_text(self):
        fig = empty_figure("Custom")
        assert fig.layout.title.text == "Custom"

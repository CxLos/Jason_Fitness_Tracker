# ============================== TEST DATA LOADER ============================ #

"""
Unit tests for ``src.data.loader``.

These tests patch the Google Sheets client so they can run offline.
"""

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.data.loader import load_data_for_year, filter_muscle_group


# ------------------------------ Fixtures ------------------------------------ #

_SAMPLE_RECORDS = [
    {
        "Date": "2026-01-05",
        "Push Exercise": "Bench Press",
        "Pull Exercise": "",
        "Leg Exercise": "",
        "Bicep Exercise": "",
        "Triceps Exercise": "",
        "Shoulder Exercise": "",
        "Forearm Exercise": "",
        "Abs Exercise": "",
        "Calisthenics Exercise": "",
        "Cardio Exercise": "",
        "Weight": 185,
        "Set 1": 10,
        "Set 2": 8,
        "Set 3": 6,
        "Set 4": "",
        "Set 5": "",
        "Time": "",
        "Distance": "",
        "Floors": "",
        "Calories": "",
    },
    {
        "Date": "2026-01-06",
        "Push Exercise": "",
        "Pull Exercise": "Lat Pulldown",
        "Leg Exercise": "",
        "Bicep Exercise": "",
        "Triceps Exercise": "",
        "Shoulder Exercise": "",
        "Forearm Exercise": "",
        "Abs Exercise": "",
        "Calisthenics Exercise": "",
        "Cardio Exercise": "",
        "Weight": 140,
        "Set 1": 12,
        "Set 2": 10,
        "Set 3": 8,
        "Set 4": "",
        "Set 5": "",
        "Time": "",
        "Distance": "",
        "Floors": "",
        "Calories": "",
    },
]


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Return a small test DataFrame that mimics Google-Sheets data."""
    df = pd.DataFrame(_SAMPLE_RECORDS)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# -------------------------------- Tests ------------------------------------- #


class TestLoadDataForYear:
    """Tests for ``load_data_for_year``."""

    @patch("src.data.loader.client")
    def test_returns_dataframe_for_all_time(self, mock_client):
        mock_sheet = MagicMock()
        mock_sheet.sheet1.get_all_records.return_value = _SAMPLE_RECORDS
        mock_client.open_by_url.return_value = mock_sheet

        result = load_data_for_year("All Time")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @patch("src.data.loader.client")
    def test_filters_by_year(self, mock_client):
        mock_sheet = MagicMock()
        mock_sheet.sheet1.get_all_records.return_value = _SAMPLE_RECORDS
        mock_client.open_by_url.return_value = mock_sheet

        result = load_data_for_year("2026")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # both records are 2026

    @patch("src.data.loader.client")
    def test_returns_empty_on_error(self, mock_client):
        mock_client.open_by_url.side_effect = Exception("API error")

        result = load_data_for_year("2026")

        assert isinstance(result, pd.DataFrame)
        assert result.empty


class TestFilterMuscleGroup:
    """Tests for ``filter_muscle_group``."""

    def test_filters_push_exercises(self, sample_df):
        result = filter_muscle_group(
            sample_df,
            "Push Exercise",
            ["Weight", "Set 1", "Set 2", "Set 3"],
        )
        assert len(result) == 1
        assert result.iloc[0]["Push Exercise"] == "Bench Press"

    def test_empty_strings_are_excluded(self, sample_df):
        result = filter_muscle_group(
            sample_df,
            "Pull Exercise",
            ["Weight"],
        )
        assert len(result) == 1
        assert result.iloc[0]["Pull Exercise"] == "Lat Pulldown"

# =================================== DATA LOADER ================================= #

"""
Functions for loading and preprocessing fitness data from Google Sheets.
"""

import traceback

import pandas as pd

from src.config import client, SHEET_URL


def load_data_for_year(year: str) -> pd.DataFrame:
    """Load and process fitness data for a specific year from Google Sheets.

    Args:
        year: A year string (e.g. ``'2026'``) or ``'All Time'`` for all data.

    Returns:
        A cleaned, sorted DataFrame. Returns an empty DataFrame on error.
    """
    try:
        data = pd.DataFrame(
            client.open_by_url(SHEET_URL).sheet1.get_all_records()
        )
        df = data.copy()

        # Normalise column names
        df.columns = df.columns.str.strip()

        # Parse dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # Filter by year
        if year == "All Time":
            filtered = df.copy()
        else:
            try:
                year_int = int(year)
            except (ValueError, TypeError):
                year_int = pd.Timestamp.now().year
            filtered = df[df["Date"].dt.year == year_int]

        # Sort chronologically
        filtered = filtered.sort_values(by="Date", ascending=True)

        # Strip whitespace from string columns
        for col in filtered.select_dtypes(include="object").columns:
            filtered[col] = filtered[col].map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        return filtered.copy()

    except Exception as e:
        print(f"❌ ERROR loading data for {year}: {e}")
        traceback.print_exc()
        return pd.DataFrame()


def filter_muscle_group(
    df: pd.DataFrame, exercise_col: str, extra_cols: list[str]
) -> pd.DataFrame:
    """Filter a DataFrame down to rows for a specific muscle group.

    Args:
        df: Full year DataFrame.
        exercise_col: The column name (e.g. ``'Push Exercise'``).
        extra_cols: Additional metric columns to keep alongside Date.

    Returns:
        Filtered DataFrame with only non-empty exercise rows.
    """
    cols = ["Date", exercise_col] + extra_cols
    available = [c for c in cols if c in df.columns]
    subset = df[available].dropna(subset=[exercise_col])
    subset = subset[subset[exercise_col].str.strip() != ""]
    return subset

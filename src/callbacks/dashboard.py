# =========================== DASHBOARD CALLBACK ============================= #

"""
Main callback that reacts to the year-dropdown selection and updates every
visual on the dashboard.
"""

from __future__ import annotations

import traceback

from dash import Input, Output

from src.config import WEIGHT_GROUPS
from src.data.loader import load_data_for_year, filter_muscle_group
from src.visuals.charts import (
    make_line_chart,
    make_bar_chart,
    make_pie_chart,
    empty_figure,
)

_EMPTY = empty_figure()

# Columns kept alongside the exercise column for weight-based groups
_WEIGHT_EXTRAS = ["Weight", "Set 1", "Set 2", "Set 3", "Set 4", "Set 5"]
_CARDIO_EXTRAS = ["Time", "Distance", "Floors", "Calories"]

# Slug mapping: exercise_col -> id slug
_SLUG_MAP = {
    "Push Exercise": "push",
    "Triceps Exercise": "tricep",
    "Pull Exercise": "pull",
    "Leg Exercise": "leg",
    "Bicep Exercise": "bicep",
    "Shoulder Exercise": "shoulder",
    "Forearm Exercise": "forearm",
    "Abs Exercise": "ab",
    "Calisthenics Exercise": "calisthenics",
}


def register_callbacks(app):
    """Attach all callbacks to *app*."""

    # Build Output list dynamically from the muscle groups
    _outputs = [
        Output("year-subtitle", "children"),
        Output("total-exercises-title", "children"),
        Output("total-exercises", "children"),
    ]

    # Per-group outputs: title, days, line, bar, pie
    for exercise_col, label in WEIGHT_GROUPS:
        slug = _SLUG_MAP[exercise_col]
        _outputs += [
            Output(f"{slug}-days-title", "children"),
            Output(f"{slug}-days", "children"),
        ]

    # Cardio rollup
    _outputs += [
        Output("cardio-days-title", "children"),
        Output("cardio-days", "children"),
    ]

    # Graph outputs (line, bar, pie) for each weight group
    for exercise_col, label in WEIGHT_GROUPS:
        slug = _SLUG_MAP[exercise_col]
        _outputs += [
            Output(f"{slug}-graph", "figure"),
            Output(f"{slug}-bar", "figure"),
            Output(f"{slug}-pie", "figure"),
        ]

    # Cardio graphs
    _outputs += [
        Output("cardio-graph", "figure"),
        Output("cardio-bar", "figure"),
        Output("cardio-pie", "figure"),
    ]

    # Table
    _outputs += [
        Output("table-title", "children"),
        Output("applications-table", "data"),
        Output("applications-table", "columns"),
    ]

    @app.callback(_outputs, [Input("year-dropdown", "value")])
    def update_dashboard(selected_year):  # noqa: C901
        # Total outputs: 3 (top) + 2*9 (weight titles) + 2 (cardio title)
        #   + 3*9 (weight graphs) + 3 (cardio graphs) + 3 (table) = 56
        n_title_pairs = len(WEIGHT_GROUPS) + 1  # +1 for cardio
        n_graph_triples = len(WEIGHT_GROUPS) + 1

        if selected_year is None:
            # Build placeholder titles for each muscle group
            group_placeholders = []
            for _, label in WEIGHT_GROUPS:
                group_placeholders += [f"Total {label} Days -", "-"]
            # Cardio placeholder
            group_placeholders += ["Total Cardio Days -", "-"]

            return (
                "-",                # year_subtitle
                "Total Gym Days -", # rollup_title
                "-",                # total
                *group_placeholders,  # title + value for each group
                *[_EMPTY] * (n_graph_triples * 3),  # line + bar + pie per group
                "Fitness Tracker Table -",  # table_title
                [],   # table_data
                [],   # table_columns
            )

        try:
            print(f"🔄 Callback triggered for year: {selected_year}", flush=True)
            df_year = load_data_for_year(selected_year)

            # ---------- Filter each muscle group --------------------------
            group_data = {}
            for exercise_col, label in WEIGHT_GROUPS:
                df_grp = filter_muscle_group(df_year, exercise_col, _WEIGHT_EXTRAS)
                group_data[exercise_col] = df_grp

            df_cardio = filter_muscle_group(
                df_year, "Cardio Exercise", _CARDIO_EXTRAS
            )

            # ---------- Compute rollup values -----------------------------
            total = df_year["Date"].nunique()

            title_values = []
            for exercise_col, label in WEIGHT_GROUPS:
                slug = _SLUG_MAP[exercise_col]
                df_grp = group_data[exercise_col]
                days = df_grp["Date"].nunique() if not df_grp.empty else 0
                title_values += [
                    f"Total {label} Days - {selected_year}",
                    days,
                ]

            # Cardio title/days
            cardio_days = df_cardio["Date"].nunique() if not df_cardio.empty else 0
            title_values += [
                f"Total Cardio Days - {selected_year}",
                cardio_days,
            ]

            # ---------- Build charts per group ----------------------------
            graph_values = []
            for exercise_col, label in WEIGHT_GROUPS:
                df_grp = group_data[exercise_col]

                line_fig = make_line_chart(
                    df_grp,
                    f"{label} Progress Over Time - {selected_year}",
                    exercise_col,
                )

                df_counts = (
                    df_grp[exercise_col]
                    .value_counts()
                    .reset_index()
                )
                df_counts.columns = [exercise_col, "Count"]

                bar_fig = make_bar_chart(
                    df_counts,
                    exercise_col,
                    f"{label} Exercise Bar Chart - {selected_year}",
                )
                pie_fig = make_pie_chart(
                    df_counts,
                    exercise_col,
                    f"{label} Exercise Distribution - {selected_year}",
                )
                graph_values += [line_fig, bar_fig, pie_fig]

            # Cardio charts
            cardio_line = make_line_chart(
                df_cardio,
                f"Cardio Progress Over Time - {selected_year}",
                "Cardio Exercise",
            )
            df_cardio_counts = (
                df_cardio["Cardio Exercise"]
                .value_counts()
                .reset_index()
            )
            df_cardio_counts.columns = ["Cardio Exercise", "Count"]

            cardio_bar = make_bar_chart(
                df_cardio_counts,
                "Cardio Exercise",
                f"Cardio Exercise Bar Chart - {selected_year}",
            )
            cardio_pie = make_pie_chart(
                df_cardio_counts,
                "Cardio Exercise",
                f"Cardio Exercise Distribution - {selected_year}",
            )
            graph_values += [cardio_line, cardio_bar, cardio_pie]

            # ---------- Table data ----------------------------------------
            df_indexed = df_year.reset_index(drop=True).copy()
            df_indexed.insert(0, "#", df_indexed.index + 1)
            table_data = df_indexed.to_dict("records")
            table_columns = [
                {"name": col, "id": col} for col in df_indexed.columns
            ]

            return (
                selected_year,
                f"Total Gym Days - {selected_year}",
                total,
                *title_values,
                *graph_values,
                f"Fitness Tracker Table - {selected_year}",
                table_data,
                table_columns,
            )

        except Exception as e:
            print(f"❌ ERROR in callback: {e}")
            traceback.print_exc()
            return (
                f"Error: {selected_year}",
                "Error loading data",
                0,
                *["Error"] * (n_title_pairs * 2),
                *[_EMPTY] * (n_graph_triples * 3),
                "Error loading table",
                [],
                [],
            )

# ============================== LAYOUT ===================================== #

"""
Assembles the full Dash ``app.layout`` from reusable components.
"""

from dash import html

from .components import (
    header_section,
    top_rollup_row,
    muscle_graph_row,
    data_table_section,
)

# Ordered list of (slug, label) for every muscle-group row.
_MUSCLE_ROWS = [
    ("push", "Push"),
    ("pull", "Pull"),
    ("leg", "Leg"),
    ("bicep", "Bicep"),
    ("tricep", "Tricep"),
    ("shoulder", "Shoulder"),
    ("calisthenics", "Calisthenics"),
    ("ab", "Ab"),
    ("forearm", "Forearm"),
    ("cardio", "Cardio"),
]


def create_layout() -> html.Div:
    """Return the complete ``app.layout`` component tree."""
    graph_rows = [muscle_graph_row(slug, label) for slug, label in _MUSCLE_ROWS]

    return html.Div(
        children=[
            header_section(),
            top_rollup_row(),
            html.Div(className="graph-container", children=graph_rows),
            data_table_section(),
        ]
    )

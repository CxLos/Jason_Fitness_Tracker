# ============================== COMPONENTS ================================= #

"""
Reusable Dash HTML component builders for the Fitness Tracker dashboard.
"""

from dash import dcc, html, dash_table

from src.config import APP_NAME, YEAR_OPTIONS, REPORT_YEAR
from src.visuals.charts import empty_figure

_EMPTY = empty_figure()


# ========================== Header / Hero =================================== #


def header_section() -> html.Div:
    """Top header bar with title, year subtitle, dropdown, and repo link."""
    return html.Div(
        className="divv",
        children=[
            html.H1(f"{APP_NAME} Fitness Tracker", className="title"),
            dcc.Loading(
                id="year-subtitle-loading",
                type="circle",
                color="red",
                style={"display": "inline-flex", "alignItems": "center", "gap": "10px"},
                children=html.H1(
                    id="year-subtitle",
                    children="-",
                    className="title2",
                    style={"margin": "0"},
                ),
            ),
            html.Div(
                className="dropdown-container",
                children=[
                    html.Label("", style={"marginRight": "10px", "fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="year-dropdown",
                        options=YEAR_OPTIONS,
                        value=None,
                        placeholder="Select Year",
                        clearable=False,
                        style={
                            "width": "150px",
                            "fontFamily": '-apple-system, BlinkMacSystemFont, "Segoe UI", Calibri, Arial, sans-serif',
                            "backgroundColor": "rgb(253, 180, 180)",
                            "border": "2px solid rgb(217, 24, 24)",
                            "borderRadius": "50px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "margin": "20px 0",
                },
            ),
            html.Div(
                className="btn-box",
                children=[
                    html.A(
                        "Repo",
                        href=f"https://github.com/CxLos/Jason_Fitness_Tracker",
                        className="btn",
                    ),
                ],
            ),
        ],
    )


# ======================= Top-Level Rollup Row =============================== #


def top_rollup_row() -> html.Div:
    """The two big rollup circles at the top (Total Gym Days + placeholder)."""
    return html.Div(
        className="rollup-row",
        children=[
            _rollup_box(
                title_id="total-exercises-title",
                value_id="total-exercises",
                default_title="Total Gym Days -",
                css_circle="circle-1",
                css_box="rollup-box-tl",
                css_circle_wrapper="circle-box-1",
            ),
            _rollup_box(
                title_id="-days-title",
                value_id="-days",
                default_title="Placeholder",
                css_circle="circle-2",
                css_box="rollup-box-tr",
            ),
        ],
    )


# ====================== Muscle-Group Graph Row ============================= #


def muscle_graph_row(
    slug: str,
    label: str,
) -> html.Div:
    """A full row for a muscle group: rollup circle + line chart + bar + pie.

    Args:
        slug: HTML-safe id prefix (e.g. ``'push'``, ``'pull'``).
        label: Display label (e.g. ``'Push'``, ``'Pull'``).
    """
    return html.Div(
        className="graph-row",
        children=[
            _rollup_box(
                title_id=f"{slug}-days-title",
                value_id=f"{slug}-days",
                default_title=f"Total {label} Days",
            ),
            html.Div(
                className="wide-box",
                children=[
                    dcc.Graph(
                        id=f"{slug}-graph",
                        className="wide-graph",
                        figure=_EMPTY,
                    )
                ],
            ),
            html.Div(
                className="graph-row-1",
                children=[
                    html.Div(
                        className="graph-box",
                        children=[
                            dcc.Graph(
                                id=f"{slug}-bar",
                                className="graph",
                                figure=_EMPTY,
                            )
                        ],
                    ),
                    html.Div(
                        className="graph-box",
                        children=[
                            dcc.Graph(
                                id=f"{slug}-pie",
                                className="graph",
                                figure=_EMPTY,
                            )
                        ],
                    ),
                ],
            ),
        ],
    )


# ========================== Data Table ====================================== #


def data_table_section() -> html.Div:
    """Bottom section with the interactive DataTable."""
    return html.Div(
        className="data-box",
        children=[
            html.H1(
                id="table-title",
                className="data-title",
                children=f"Fitness Tracker Table {REPORT_YEAR}",
            ),
            dash_table.DataTable(
                id="applications-table",
                data=[],  # type: ignore
                columns=[],  # type: ignore
                page_size=20,
                sort_action="native",
                filter_action="native",
                row_selectable="multi",
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "minWidth": "100px",
                    "whiteSpace": "normal",
                },
                style_header={
                    "textAlign": "center",
                    "fontWeight": "bold",
                    "backgroundColor": "#FF0000",
                    "color": "white",
                },
                style_data={"whiteSpace": "normal", "height": "auto"},
                style_cell_conditional=[  # type: ignore
                    {
                        "if": {"column_id": "#"},
                        "style": {
                            "width": "20px",
                            "minWidth": "60px",
                            "maxWidth": "60px",
                            "textAlign": "center",
                        },
                    },
                    {
                        "if": {"column_id": "Description"},
                        "style": {"width": "350px", "minWidth": "200px", "maxWidth": "400px"},
                    },
                    {
                        "if": {"column_id": "Tags"},
                        "style": {"width": "250px", "minWidth": "200px", "maxWidth": "400px"},
                    },
                    {
                        "if": {"column_id": "Collab"},
                        "style": {"width": "250px", "minWidth": "200px", "maxWidth": "400px"},
                    },
                ],
            ),
        ],
    )


# ========================== Private Helpers ================================= #


def _rollup_box(
    title_id: str,
    value_id: str,
    default_title: str,
    css_circle: str = "circle",
    css_box: str = "rollup-box",
    css_circle_wrapper: str = "circle-box",
) -> html.Div:
    """A single rollup stat box with a title and a circle number."""
    return html.Div(
        className=css_box,
        children=[
            html.Div(
                className="title-box",
                children=[
                    html.H3(
                        id=title_id,
                        className="rollup-title",
                        children=[default_title],
                    ),
                ],
            ),
            html.Div(
                className=css_circle_wrapper,
                children=[
                    html.Div(
                        className=css_circle,
                        children=[
                            html.H1(
                                id=value_id,
                                className="rollup-number",
                                children=["-"],
                            ),
                        ],
                    )
                ],
            ),
        ],
    )

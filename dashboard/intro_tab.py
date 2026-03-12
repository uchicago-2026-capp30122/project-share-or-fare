import html

import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from app import dropdown_options
from dash import dcc, html

from .visualization.transform import get_text

# Load text and data
data_text = get_text("dashboard/text/data.txt")
intro_text = get_text("dashboard/text/intro.txt")


# Prep Ineractive Altair Histogram
alt_hist = (
    dvc.Vega(
        id="altair-hist",
        opt={"renderer": "svg", "actions": False},
        spec={},
        style={"display": "flex", "justifyContent": "center", "width": "100%"},
    ),
)
hist_title = html.Div(id="hist_title", children=[])


# Page components
intro = [
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.H1(children="Share or Fare?", style={"fontSize": "48px"}),
    html.Div(
        children="A Comparison of Ride Share Usage and Transit Routes in Chicago",
        style={"fontSize": "32px"},
    ),
    html.Hr(),
    html.H5(
        children="Molly Long, Waleed Shahzad, Sabrina Wang, Sarah Zebar",
        style={"color": "grey"},
    ),
    html.H5(children="CAPP 30122 Winter 2026", style={"color": "grey"}),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.Div(children=intro_text, style={"white-space": "pre-wrap"}),
]

intro_histogram = [
    html.Hr(),
    html.H3(children="A Brief Overview of Our Data"),
    html.Div(children=data_text, style={"white-space": "pre-wrap"}),
    html.Div(
        children="There were 93,510,249 rideshare rides in Chicago in 2025. Our random sample contains 15,341,421 rides."
    ),
    html.Hr(),
    dbc.Col(
        children=[
            dbc.Row(
                dbc.Col(
                    children=[
                        html.Hr(),
                        html.Div(
                            "Please select what metric you would like to see the distribution of:"
                        ),
                        dcc.Dropdown(
                            options=dropdown_options,
                            value="rideshareTime",
                            id="xaxis-column",
                        ),
                    ],
                    width={"size": 6, "offset": 3},
                )
            ),
            dbc.Row(
                [
                    html.Hr(),
                    html.H5(hist_title, style={"textAlign": "center"}),
                    html.Div(alt_hist),
                ]
            ),
        ],
    ),
]


intro_page = [
    html.Div(
        [
            dbc.Row(
                dbc.Col(
                    children=[
                        dbc.Stack(
                            [
                                dbc.Row(intro),
                                dbc.Row(intro_histogram),
                            ],
                            gap=3,
                        ),
                        html.Hr(),
                        html.Hr(),
                    ],
                    width={"size": 10, "offset": 1},
                )
            ),
        ]
    )
]

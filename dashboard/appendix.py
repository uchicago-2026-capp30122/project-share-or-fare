import pandas as pd
import html
from dash import html
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from .visualization.transform import log_transform_time, get_text
from .visualization.altair_charts import rides_by_month

df = pd.read_csv("./data/rideshare_transit_data.csv")
df = log_transform_time(df)

# Seasonality Charts
rides_by_month_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=rides_by_month(df).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"},
)

sampling_text = get_text("dashboard/text/sampling.txt")
graph_sampling_text = get_text("dashboard/text/graph_sampling.txt")
seasonal_text = get_text("dashboard/text/seasonal.txt")


graph_sampling = [
    html.Hr(),
    html.Hr(),
    html.H3("Random Subset to Reduce Load on Graphs"),
    html.Hr(),
    html.Div([graph_sampling_text]),
]

seasonality = [
    html.Hr(),
    html.Hr(),
    html.H3("Future Extensions: Seasonality Trends in Rideshare Usage"),
    html.Hr(),
    html.Div([seasonal_text]),
    html.Hr(),
    dbc.Row(
        [
            html.H5("Average Rides per Day by Month", style={"textAlign": "center"}),
            html.Div([rides_by_month_chart]),
        ]
    ),
    html.Hr(),
    html.Hr(),
]

html.Div(children=sampling_text, style={"white-space": "pre-wrap"})

appendix = [
    html.Div(
        [
            dbc.Row(
                dbc.Col(
                    children=[
                        dbc.Stack(
                            [
                                dbc.Row(
                                    [
                                        html.Hr(),
                                        html.Hr(),
                                        html.H3("Sampling Methodology"),
                                        html.Hr(),
                                        html.Div(
                                            children=sampling_text,
                                            style={"white-space": "pre-wrap"},
                                        ),
                                        html.Hr(),
                                    ]
                                ),
                                dbc.Row(graph_sampling),
                                dbc.Row(seasonality),
                            ],
                            gap=3,
                        )
                    ],
                    width={"size": 10, "offset": 1},
                )
            ),
        ]
    )
]

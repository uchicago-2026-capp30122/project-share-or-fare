# from flask import Flask, request, jsonify
# import folium
# import branca
# from folium import GeoJson, GeoJsonTooltip
import pandas as pd
from shapely import from_wkt
import html
from dash import html, dcc
# import numpy as np
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import altair as alt
import dash_vega_components as dvc
from .visualization.transform import log_transform_time, get_text
from .visualization.altair_charts import(
    weighted_avg,
    # most_pickups,
    distance_vs_demand_quadrants,
    # corridor_bar_chart,
    transit_penalty_heatmap,
    rideshare_count_heatmap,
    corridor_highest_price,
    corridor_lowest_price,
    distribution_of_rides,
    distribution_of_ratio,
    transit_rideshare_comparison,
    rides_by_month
)



df = pd.read_csv('./data/rideshare_transit_data.csv')
df = log_transform_time(df)

alt.data_transformers.disable_max_rows()

# Rideshare to Transit Time Comparison
ride_by_transit = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=transit_rideshare_comparison(df).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

distribution_of_ratio_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=distribution_of_ratio(df).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

ratio_intro_text = get_text('dashboard/text/ratio_intro.txt')
transit_penalty_text = get_text('dashboard/text/transit_penalty.txt')

ratio = [
    dbc.Col(children=[
        html.Hr(),
        html.H3("Comparing Public Transportation Trip Time to Rideshare Trip Time"),
        html.Hr(),
        html.Hr(),
        html.Div([ratio_intro_text]),
        html.Hr(),
        dbc.Row([
            html.H5(
                "Comparison of Public Tranportation and Rideshare Trip times",
                style={'textAlign': 'center'}
            ),
            html.Div([ride_by_transit]),
        ], justify="center", align="center"),
        html.Hr(),
        html.Hr(),
        html.Div(dcc.Markdown(transit_penalty_text)),
        html.Hr(),
        dbc.Row([
            html.H5(
                "Distribution of Ratio of Transit to Rideshare Time",
                style={'textAlign': 'center'}
            ),
            html.Div([distribution_of_ratio_chart]),
        ], justify="center", align="center"),
        html.Hr(),
        html.Hr(),
    ],
    width={"size": 10, "offset": 1}
    )
]
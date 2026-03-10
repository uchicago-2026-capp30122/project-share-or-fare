# from flask import Flask, request, jsonify
# import folium
# import branca
# from folium import GeoJson, GeoJsonTooltip
import pandas as pd
from shapely import from_wkt
import html
from dash import html, dcc
# import numpy as np
# import dash_ag_grid as dag
import dash_bootstrap_components as dbc
# import altair as alt
import dash_vega_components as dvc
from .visualization.transform import log_transform_time, get_text

data_text = get_text('dashboard/text/data.txt')
intro_text = get_text('dashboard/text/intro.txt')

df = pd.read_csv('./data/rideshare_transit_data.csv')
df = log_transform_time(df)

dropdown_options={
    'rideshareTime': 'Rideshare Trip Time (Minutes)',
    'totalTransitTime': 'Corresponding Transit Trip Time (Minutes)',
    "Log Rideshare Min": "Log of Rideshare Trip Time (Minutes)",
    "Log Transit Min": "Log of Transit Trip Time (Minutes)",
    "Float Trip Miles": "Rideshare Trip Distance (Miles)"
}


# Page components
intro = [
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.H1(children='Share or Fare?', style={'fontSize': '48px'}),
    html.Div(
        children='A Comparison of Ride Share Usage and Transit Routes in Chicago',
        style={'fontSize': '32px'}),
    html.Hr(),
    html.H5(
        children='Molly Long, Waleed Shahzad, Sabrina Wang, Sarah Zebar',   style={'color': 'grey'}
    ),
    html.H5(
        children='CAPP 30122 Winter 2026',
        style={'color': 'grey'}
    ),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.Div(children=intro_text, 
             style={'white-space': 'pre-wrap'})
]


# Altair Histogram
alt_hist = dvc.Vega(
    id="altair-hist",
    opt={"renderer": "svg", "actions": False},
    spec={},
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
),

hist1 = [
    html.Hr(),
    html.H3(children='A Brief Overview of Our Data'),
    html.Div(children=data_text,
             style={'white-space': 'pre-wrap'}),
    html.Div(children="There were 93,510,249 rideshare rides in Chicago in 2025. Our random sample contains 15,341,421 rides."),
    html.Hr(),
    html.Hr(),
    html.H3("Distribution of Rideshare Data"),
    dbc.Col(children=[
        dbc.Row(dbc.Col(children=[
            html.Hr(),
            html.Div("Please select what metric you would like to see the distribution of:"),
            dcc.Dropdown(
            options=dropdown_options,
            value='rideshareTime',
            id='xaxis-column'
            )
        ], width={"size": 6, "offset": 3})),
        dbc.Row([
            html.Hr(),
            html.Div(alt_hist)
        ]),
    ],
    )
]


exploratory = [html.Div([
    dbc.Row(dbc.Col(
        children=[
            dbc.Stack([
                dbc.Row(intro),
                dbc.Row(hist1),
            ], gap = 3),
            html.Hr(),
            html.Hr()
        ],
        width={"size": 10, "offset": 1},
    )), 
])]
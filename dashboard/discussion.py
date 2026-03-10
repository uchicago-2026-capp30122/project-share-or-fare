from flask import Flask, request, jsonify
import folium
import branca
from folium import GeoJson, GeoJsonTooltip
import pandas as pd
from shapely import from_wkt
import html
from dash import Dash, html, dcc, callback, Output, Input
import numpy as np
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import altair as alt
import dash_vega_components as dvc
from .visualization.transform import log_transform_time, get_text


discussion_text = get_text('dashboard/text/discussion.txt')

discussion = [dbc.Col(children=[
    html.Hr(),
    html.H3("Discussion of Results"),
    html.Hr(),
    html.Div(
        children=discussion_text,
        style={"white-space": "pre-wrap"}
    )
], width={"size": 10, "offset": 1})]
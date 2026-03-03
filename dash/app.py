# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import numpy as np
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import altair as alt
import dash_vega_components as dvc

################################################################################
#
# To run the dash app, from base project-share-or-fare directory run
#   `uv run dash/app.py -m`
#
# `ctrl c` to stop running the app.
#
################################################################################

# Initialize the app
app = Dash(external_stylesheets=[dbc.themes.LUX])

# Data Processing
df = pd.read_csv('./data/small_medium_merged.csv')

# Drop all NAs
df = df.replace("NaN", np.nan)
df = df.dropna()

df["totalTime"] = df["totalTime"].str[:-1]
df["totalTime"] = df["totalTime"].astype('Int64')
df["totalTimeMin"] = df["totalTime"] / 60
df["Average Trip Minutes"] = df["Average Trip Seconds"] / 60

df["Number of Modes"] = df["modes"].str.split(",").apply(len)

p = """This is a project looking at rideshare data and the transit alternatives to rideshare rides. Our data is a random sample of all rideshare rides within the City of Chicago in the calendar year 2025. We will look at the distribution of rides in our dataset, the distribution of transit alternative, and try to discover why people choose to take rideshare instead of public transportation.
"""
dropdown_options={
    'Average Trip Minutes': 'Rideshare Time',
    'totalTimeMin': 'Corresponding Transit Time',
}

# Page components
intro = [
    html.Hr(),
    html.Hr(),
    html.H1(children='Project Share or Fare'),
    html.Div(children=p)
]

# Altair Histogram
alt_hist = dvc.Vega(
    id="altair-hist", opt={"renderer": "svg", "actions": False}, spec={}
),

hist1 = [
    html.Hr(),
    html.H3("Distribution of Rideshare Data"),
    dbc.Col(children=[
        dbc.Row([
            dbc.Col(
                alt_hist
            ),
            dbc.Col([
                html.Hr(),
                html.Div("Please select what metric you would like to see the distribution of:"),
                dcc.Dropdown(
                options=dropdown_options,
                value='Average Trip Minutes',
                id='xaxis-column'
                )
            ])
        ])
    ])
]

# Minutes time
alt.data_transformers.disable_max_rows()
chart1 = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x="Average Trip Minutes",
        y="Average Trip Total",
    )
    .interactive()
)
scatter_time = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart1.to_dict(),
)

# Price by Distance
chart2 = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x="Float Trip Miles",
        y="Average Trip Total",
    )
    .interactive()
)
scatter_dist = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart2.to_dict(),
)


# Ride by transit alternative
alt.data_transformers.disable_max_rows()
chart3 = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        x="Average Trip Minutes",
        y="totalTimeMin",
    )
    .interactive()
)
ride_by_transit = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart3.to_dict(),
)

# number of transit modes
chart4 = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        alt.X("sum(Count):Q").title("Number of Rides"),
        alt.Y("Number of Modes:O")
    )
)
bar_modes = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart4.to_dict(),
)

# Display all other visualizations
other_viz = [
    html.Hr(),
    html.H3("Other Exploratory Visualizations"),
    html.Hr(),
    dbc.Row([
        html.H5("Trip Price by Length of Ride in Minutes"),
        html.Div([scatter_time]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Trip Price by Distance of Ride"),
        html.Div([scatter_dist]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Transit Alternative Time by Rideshare Time"),
        html.Div([ride_by_transit]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Number of modes for transit alternative"),
        html.Div([bar_modes]),
    ]),
]


# App layout
app.layout = [html.Div([
    dbc.Row(dbc.Col(
        children=[
            dbc.Stack([
                dbc.Row(intro),
                dbc.Row(hist1),
                dbc.Row(other_viz),
                dbc.Row([html.Hr(), html.Hr()])
            ], 
            gap = 3)],
        width={"size": 10, "offset": 1},
    )),  
])
]

# Add controls to build the interaction
@callback(
    Output(component_id='altair-hist', component_property='spec'),
    Input(component_id='xaxis-column', component_property='value')
)
def update_graph(row_chosen):
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X(f"{row_chosen}:Q", title=dropdown_options[row_chosen]),
            alt.Y("sum(Count):Q", title="Number of Rides"),
        )
        .interactive()
    )

    return chart.to_dict()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

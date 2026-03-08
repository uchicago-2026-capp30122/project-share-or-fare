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
df = pd.read_csv('./data/small_medium_merged.csv')[:3000]

# Drop all NAs
df = df.replace("NaN", np.nan)
df = df.dropna()

df["totalTime"] = df["totalTime"].str[:-1]
df["totalTime"] = df["totalTime"].astype('Int64')
df["totalTimeMin"] = df["totalTime"] / 60
df["Average Trip Minutes"] = df["Average Trip Seconds"] / 60

df["Number of Modes"] = df["modes"].str.split(",").apply(len)

df["Transit Percentage Longer"] = ((df["totalTimeMin"] - df["Average Trip Minutes"]) / df["Average Trip Minutes"]).round(1)
df["Transit Rideshare Ratio"] = (df["totalTimeMin"] / df["Average Trip Minutes"]).round(1)

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


# Ride by transit alternative
alt.data_transformers.disable_max_rows()
ratio_1_line = pd.DataFrame(
    {'Average Trip Minutes': [0, 100], 'totalTimeMin': [0, 100]}
)
ratio_title = "Trip Time of Public Transportation Alternative to Rideshare"
chart3 = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(
        alt.X("Average Trip Minutes:Q")
            .title("Trip Time via Rideshare (Minutes)")
            .scale(domain=[0, 100]),
        alt.Y("totalTimeMin:Q")
            .title("Trip Time via Public Transportation (Minutes)")
            .scale(domain=[0, 100])
    )
    .interactive() +
    alt.Chart(ratio_1_line)
    .mark_line(color='lightgray', thickness=0.2)
    .encode(
        x='Average Trip Minutes', y='totalTimeMin'
    )
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

# Transit percentage longer
vline_data = pd.DataFrame({'x': [50]})
vline = alt.Chart(vline_data).mark_rule(color='red', strokeWidth=3).encode(x='x:Q')

chart5 = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        alt.X(
            "Transit Rideshare Ratio:O", 
            title="Difference in Transit and Ridehsare Time as Percentage of Rideshare time"),
        alt.Y("sum(Count):Q", title="Number of Rides"),
    )
    .interactive() 
    + 
    alt.Chart(pd.DataFrame({'Transit Rideshare Ratio': [1]}))
    .mark_rule(color='red')
    .encode(x='Transit Rideshare Ratio:O')
)
hist_time_ratio = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart5.to_dict(),
)



# Display all other visualizations
other_viz = [
    html.Hr(),
    html.H3("Other Exploratory Visualizations"),
    html.Hr(),
    dbc.Row([
        html.H5("Comparison of Public Tranportation and Rideshare Trip times"),
        html.Div([ride_by_transit]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Number of modes for transit alternative"),
        html.Div([bar_modes]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.H5("Distribution of Transit Alternative to Rides as Ratios"),
        html.Div([hist_time_ratio]),
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

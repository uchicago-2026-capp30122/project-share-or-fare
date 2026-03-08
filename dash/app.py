# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import numpy as np
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import altair as alt
import dash_vega_components as dvc
from visualization.transform_data import clean_and_transform
from visualization.altair_charts import(
    chart1,
    chart2,
    chart3,
    price_chart,
    chart5,
    distribution_of_rides,
    distribution_of_ratio,
    transit_rideshare_comparison,
    rides_by_month,
    ratio_by_month
)


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
df = clean_and_transform(df)

p = """This is a project looking at rideshare data and the transit alternatives to rideshare rides. Our data is a random sample of all rideshare rides within the City of Chicago in the calendar year 2025. We will look at the distribution of rides in our dataset, the distribution of transit alternative, and try to discover why people choose to take rideshare instead of public transportation.
"""
dropdown_options={
    'Average Trip Minutes': 'Rideshare Time',
    'totalTimeMin': 'Corresponding Transit Time',
    "Log Rideshare Min": "Log Rideshare Min",
    "Log Transit Min": "Log Transit Min"
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


# Visualizations
alt.data_transformers.disable_max_rows()

ride_by_transit = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=transit_rideshare_comparison(df).to_dict(),
)

distribution_of_ratio_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=distribution_of_ratio(df).to_dict(),
)

rides_by_month_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=rides_by_month(df).to_dict(),
)

ratio_by_month_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=ratio_by_month(df).to_dict(),
)

# Waleed Charts
top_neighborhoods = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart1.to_dict(),
)

distance_ride_neighborhood = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart2.to_dict(),
)

conectivity_pairs = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=chart3.to_dict(),
)

price_corridor_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=price_chart.to_dict(),
)

connectivity_trips = dvc.Vega(
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
        html.H5("Distribution of Ratio of Transit to Rideshare Time"),
        html.Div([distribution_of_ratio_chart]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Average Rides per Day by Month"),
        html.Div([rides_by_month_chart]),
    ]),
    html.Hr(),
    dbc.Row([
        html.H5("Change in Transportation Time to Rideshare Time Ratio Over Time Compared to Temperature"),
        html.Div([ratio_by_month_chart]),
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([top_neighborhoods]),
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([distance_ride_neighborhood]),
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([conectivity_pairs]),
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([price_corridor_chart]),
    ]),
    html.Hr(),
    dbc.Row([
        html.Div([connectivity_trips]),
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
    chart = distribution_of_rides(df, row_chosen, dropdown_options)
    # chart = (
    #     alt.Chart(df)
    #     .mark_bar()
    #     .encode(
    #         alt.X(f"{row_chosen}:Q", title=dropdown_options[row_chosen]),
    #         alt.Y("sum(Count):Q", title="Number of Rides"),
    #     )
    #     .interactive()
    # )

    return chart.to_dict()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

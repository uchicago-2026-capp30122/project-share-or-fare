# Import packages
from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

################################################################################
#
# To run the dash app, from base project-share-or-fare directory run
#   `uv run dash/app.py -m`
#
################################################################################

app = Dash(external_stylesheets=[dbc.themes.LUX])

# Incorporate data
df = pd.read_csv('./data/small_medium_merged.csv')
df["totalTime"] = df["totalTime"].str[:-1]
df["totalTime"] = df["totalTime"].astype('Int64')
df["totalTime"] = df["totalTime"] / 60

# Initialize the app
app = Dash()

fig = px.histogram(df, x="totalTime", 
                   nbins=40, 
                   title='Distribution of Transit Times',
                   labels={'totalTime':'Transit Time (Minutes)',
                           'count':'Number of Rides'}
                   )

p = """This is a project looking at rideshare data and the transit alternatives to rideshare rides. Our data is a random sample of all rideshare rides within the City of Chicago in the calendar year 2025. We will look at the distribution of rides in our dataset, the distribution of transit alternative, and try to discover why people choose to take rideshare instead of public transportation.
"""

# App layout
app.layout = [
    html.H1(children='Project Share or Fare'),
    html.Div(children=p),
    html.H3("Distribution of Rideshare Data"),
    html.Div("Please select what metric you would like to see the distribution of:"),
    dcc.RadioItems(options=['totalTime', 'Average Trip Seconds'], value='totalTime', id='controls-and-radio-item'),
    dcc.Graph(figure={}, id='controls-and-graph'),
    html.H3("Rideshare and Transit Dataset"),
    dag.AgGrid(
        rowData=df.to_dict('records'),
        columnDefs=[{"field": i} for i in df.columns]
    )
]


# Add controls to build the interaction
@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
def update_graph(row_chosen):
    fig = px.histogram(df, x=row_chosen, 
                   nbins=40, 
                   # title='Distribution of Transit Times',
                   labels={#'totalTime':'Transit Time (Minutes)',
                           'count':'Number of Rides'}
                   )
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

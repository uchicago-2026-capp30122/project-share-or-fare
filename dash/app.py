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
# `ctrl c` to stop running the app.
#
################################################################################

# Initialize the app
app = Dash(external_stylesheets=[dbc.themes.LUX])

# Incorporate data
df = pd.read_csv('./data/small_medium_merged.csv')
df["totalTime"] = df["totalTime"].str[:-1]
df["totalTime"] = df["totalTime"].astype('Int64')
df["totalTime"] = df["totalTime"] / 60
df["Average Trip Seconds"] = df["Average Trip Seconds"] / 60

p = """This is a project looking at rideshare data and the transit alternatives to rideshare rides. Our data is a random sample of all rideshare rides within the City of Chicago in the calendar year 2025. We will look at the distribution of rides in our dataset, the distribution of transit alternative, and try to discover why people choose to take rideshare instead of public transportation.
"""

intro = [
    html.Hr(),
    html.Hr(),
    html.H1(children='Project Share or Fare'),
    html.Div(children=p)
]

hist1 = [
    html.Hr(),
    html.H3("Distribution of Rideshare Data"),
    dbc.Col(children=[
        dbc.Row([
            dbc.Col(
                dcc.Graph(figure={}, id='controls-and-graph'),
                width={"size": 8}
            ),
            dbc.Col([
                html.Hr(),
                html.Div("Please select what metric you would like to see the distribution of:"),
                dcc.Dropdown(
                options={
                    'Average Trip Seconds': 'Rideshare Time',
                    'totalTime': 'Corresponding Transit Time',
                },
                value='Average Trip Seconds',
                id='xaxis-column'
                )
            ])
        ])
    ])
]

data_table = [
    html.H3("Rideshare and Transit Dataset"),
    dag.AgGrid(
        rowData=df.to_dict('records'),
        columnDefs=[{"field": i} for i in df.columns]
    )
]


# App layout
app.layout = [html.Div([
    dbc.Row(dbc.Col(
        children=[
            dbc.Stack([
            dbc.Row(intro),
            dbc.Row(hist1),
            dbc.Row(data_table)], 
            gap = 3)],
        width={"size": 10, "offset": 1},
    )),  
])
]

# Add controls to build the interaction
@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='xaxis-column', component_property='value')
)
def update_graph(row_chosen):
    fig = px.histogram(
        df, 
        x=row_chosen, 
        y="Count", 
        histfunc='sum',
        nbins=40, 
        title='Distribution of Rides by Trip Time',
        labels={'totalTime':'Corresponding Transit Time (Minutes)',
                'Average Trip Seconds': 'Rideshare Time (Minutes)'
        }
    )

    fig.update_layout(
        yaxis_title="Number of Rides",
        title_x=0.5) 
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

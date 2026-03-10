from flask import Flask, request, jsonify
import folium
from folium import GeoJson, GeoJsonTooltip
import pandas as pd
from shapely import from_wkt
import html
from dash import Dash, html, dcc, callback, Output, Input
import numpy as np
# import dash_ag_grid as dag
import dash_bootstrap_components as dbc
# import altair as alt
# import dash_vega_components as dvc
from .visualization.transform import log_transform_time, get_text
from .visualization.altair_charts import(
    weighted_avg,
    distribution_of_rides,
)

# Import static Components
from .js import JS_CODE, CSS_STYLING
from .intro_tab import exploratory
from .tab1_transit_rideshare import ratio
from .tab2_neighborhood_analysis import neighborhood_tab
from .appendix import appendix
from .discussion import discussion


################################################################################
#
# To run the dash app, from base project-share-or-fare directory run
#   `uv run dash/app.py -m`
#
# `ctrl c` to stop running the app.
#
################################################################################


#### Interactive Map (Tab 3) ###
server = Flask(__name__)
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.LUX])


neighborhood_boundaries = pd.read_csv("data/Neighborhoods_2012b_20260227.csv")
neighborhood_route_data = pd.read_csv("data/neighborhood_route_data.csv")

# Get Pickup Neighbhorhood level data and take weighted averages
pickup_neighborhoods = neighborhood_route_data.groupby(["Pickup Neighborhood"]).apply(
    lambda g: pd.Series({
        'totalTransitTime_wavg': weighted_avg(g, 'totalTransitTime_wavg', 'Count'),
        'rideshareTime_wavg': weighted_avg(g, 'rideshareTime_wavg', 'Count'),
        'tripCost_wavg': weighted_avg(g, "tripCost_wavg", 'Count'),
        'transitPenalty_wavg': weighted_avg(g, "transitPenalty_wavg", 'Count'),
        "distance_wavg": weighted_avg(g, "distance_wavg", "Count"),
        'Count': g['Count'].sum()
    })
    ).reset_index()


current_neighborhood = ""

def standardize(x):
    """
    Standardizes value, used as weighting function for line weight
    """
    return (x-x.min())/(x.max()-x.min())


def filter_neighborhood(neighborhood):
    """
    Helper function for filtering data to specific pickup neighborhood
    """

    # Don't want to include intra-neighborhood rides
    filtered_neighborhood_routes = neighborhood_route_data[
        (neighborhood_route_data['Pickup Neighborhood'] == neighborhood) &
        (neighborhood_route_data['Dropoff Neighborhood'] != neighborhood)
        ].sort_values("Count", ascending=False)

    # Add percentage of rides from pickup to each neighborhood
    filtered_neighborhood_routes["perc_rides"] = round((
        filtered_neighborhood_routes["Count"]/filtered_neighborhood_routes["Count"].sum())*100, 2)
    
    # Add opacity based on percentage of rides
    filtered_neighborhood_routes["line_weight"] = standardize(filtered_neighborhood_routes["perc_rides"])

    return filtered_neighborhood_routes



@server.route('/set_neighborhood', methods=['POST'])
def set_neighborhood():
    """
    Sets the current neighborhood global variable
    """
    global current_neighborhood
    current_neighborhood = request.get_json().get('name')
    return jsonify({"status": "ok"})


@server.route('/neighborhood', methods=['POST'])
def neighborhood():
    """
    Returns a JSON of the geometries for the top 5 routes originating from 
    current_neighborhood
    """

    # Use global
    global current_neighborhood


    # Filter routes dataframe for this neighborhood
    filtered_neighborhood_routes = filter_neighborhood(current_neighborhood)

    # Use only top 5 destinations
    top5_destinations = filtered_neighborhood_routes.sort_values(
        "Count", ascending=False).head(5)

    # Add geometries and features of each destination to dictionary
    features = []
    for _, row in top5_destinations.iterrows():
        pickup_poly = from_wkt(row["Pickup Neighborhood Polygon"])
        dropoff_poly = from_wkt(row["Dropoff Neighborhood Polygon"])
        features.append({
            "type": "Feature",
            "properties": {"line_weight": (row["line_weight"]*5)+1,
                           "opacity": 1,
                           "color": row["transitPenaltyColor"],
                           "from": row["Pickup Neighborhood"],
                           "to": row["Dropoff Neighborhood"],
                           "transitTime": round(row["totalTransitTime_wavg"],2),
                           "rideshareTime": round(row["rideshareTime_wavg"],2),
                           "ratio": round(row["transitPenalty_wavg"],2),
                           "n_rides": row["Count"],
                           "perc_rides": row["perc_rides"]},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [pickup_poly.centroid.x, pickup_poly.centroid.y],  # GeoJSON is [lon, lat]
                    [dropoff_poly.centroid.x,  dropoff_poly.centroid.y]
                ]
            }
        })

    return jsonify({
        "name": current_neighborhood,
        "routes": {
            "type": "FeatureCollection",
            "features": features
        }
    })
    


@server.route('/')
def make_map():
    """
    Makes the Folium map + Chicago neighborhood boundaries, and injects
    CSS styling and Javascript code to handle drawing the routes on click
    """
    # Initialize Folium Map of Chicago
    m = folium.Map(
        location=(41.86721, -87.63231),
        zoom_control=False,
        tiles="Cartodb Positron",
        zoom_start=11, 
        
    )

    # Plot neighborhood boundaries
    features = []
    for _, row in neighborhood_boundaries.iterrows():
        geom = from_wkt(row["the_geom"])
        features.append({
            "type": "Feature",
            "properties": {"name": row["PRI_NEIGH"]},
            "geometry": geom.__geo_interface__
        })

    boundaries = {"type": "FeatureCollection", "features": features}

    GeoJson(
        boundaries,
        tooltip=GeoJsonTooltip(fields=["name"], aliases=[""]),
        style_function=lambda f: {'fillOpacity': 0.2, 'weight': 1.5, 'color': '#2a6ebb'},
        highlight_function=lambda f: {'fillOpacity': 0.5},
    ).add_to(m)


    m.get_root().html.add_child(folium.Element(CSS_STYLING))
    m.get_root().html.add_child(folium.Element(JS_CODE))
    html_str = m._repr_html_()

    return html_str


@app.callback(
    Output("panel-title", "children"),
    Output("panel-content", "children"),
    Input("poll-interval", "n_intervals")
)
def update_panel(n):
    """
    This updates the panel on the top right when a neighboorhood is clicked.
    """
    global current_neighborhood

    if not current_neighborhood:
        return "Click a neighborhood", "No neighborhood selected"

    # Get filtered neighborhood dataframe
    filtered_neighborhood_routes = filter_neighborhood(current_neighborhood)

    if len(filtered_neighborhood_routes) == 0:
        return f"{current_neighborhood}", "No Data"

    # Add in some neighborhood stats, weighted by count
    avg_tripDiffRatio = str(round(
        np.average(filtered_neighborhood_routes["transitPenalty_wavg"], 
           weights=filtered_neighborhood_routes["Count"]),
        2))
    
    avg_tripCost = str(round(
        np.average(filtered_neighborhood_routes["tripCost_wavg"], 
           weights=filtered_neighborhood_routes["Count"]),
          2)).ljust(5, '0')
    

    # get just top 5 destinations
    top5_destinations = filtered_neighborhood_routes.sort_values(
        "Count", ascending=False).head(5)
    
    top5 = []
    for i in range(len(top5_destinations)):
        ngb = top5_destinations[["Dropoff Neighborhood"]].values[i][0]
        perc = top5_destinations[["perc_rides"]].values[i][0]
        ratio = round(top5_destinations[["transitPenalty_wavg"]].values[i][0],2)
        str_item = f"""{i+1}. {ngb} ({perc}% of rides) """
        top5.append(str_item)

    top5_repr = "\n".join(top5)

    return f"{current_neighborhood}", dcc.Markdown(f"""
**Top 5 destinations:** \n
{top5_repr}

**Transit Penalty Score:** \n {avg_tripDiffRatio} \n

**Average Trip Cost:** \n ${avg_tripCost}
""")

map_display = html.Div([

    # Left column - header + map
    html.Div([

        # Header
        html.Div([
            html.H1("Share or Fare? A comparison of ride share usage and transit routes in Chicago", style={"margin": "0", "color": "white", "fontSize": "24px"}),
            html.P("Molly Long, Sabrina Wang, Sarah Zebar, Waleed Shahzad", style={"margin": "0", "color": "white", "fontSize": "16px"}),
            html.P("CAPP 30122 Winter 2026", style={"margin": "0", "color": "white", "fontSize": "16px"}),
        ], style={
            "backgroundColor": "#3c83ca",
            "padding": "10px 20px",
            "borderBottom": "1px solid #ccc",
            "marginRight": "8px"
        }),

        # Map
        html.Div([
            html.Iframe(
                id="folium-map",
                srcDoc=make_map(),
                width="100%",
                height="100%",
                style={"border": "none", "display": "block"}
            )
        ], style={
            "overflow": "hidden",
            "flex": "1"            
        }),

        # Footer
        html.P("Sources: Chicago Data Portal (2025) and Google Routes API", style = {"color": "black"})

    ], style={
        "display": "flex",
        "flexDirection": "column",  
        "flex": "8",                
    }),

    # Right column containing two panels
    html.Div([

        # Top right panel - dynamic
        html.Div([
            html.H3(id="panel-title", children="Click a neighborhood"),
            html.Div(id="panel-content", children="No neighborhood selected"),
        ], style={
            "border": "2px solid #ccc",
            "borderRadius": "8px",
            "padding": "15px",
            "flex": "1",
            "overflowY": "auto",
            "boxShadow": "2px 2px 8px rgba(0,0,0,0.1)",
            "marginBottom": "10px"
        }),

        # Bottom right panel - static
        html.Div([
            html.H3("Legend"),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "green",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 0.7 - 2")]),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "yellow",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 2 - 2.35")]),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "orange",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 2.4 - 2.8")]),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "red",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 2.8+")]),
            html.P(dcc.Markdown("""**Transit Penalty Score** is the average ratio of transit time to
                        ride share time across all routes originating from a given neighborhood. For example,
                        a score of 2 means that, on average, the comparable transit route is twice as long as
                        the ride share trip. Buckets (colors) are computed based on quartiles. """)),
        ], style={
            "border": "2px solid #ccc",
            "borderRadius": "8px",
            "padding": "15px",
            "flex": "1",
            "overflowY": "auto",
            "boxShadow": "2px 2px 8px rgba(0,0,0,0.1)",
        }),

        dcc.Interval(id="poll-interval", interval=500, n_intervals=0)

    ], style={
        "display": "flex",
        "flexDirection": "column",
        "flex": "2",
        "gap": "10px"
    })

], style={
    "display": "flex",
    "flexDirection": "row",     # ← left column and right column side by side
    "height": "calc(100vh - 16px)",
    "overflow": "hidden",
    "overscrollBehavior": "none"
})


################################################################################
# Intro tab: Interactive Dropdown
###############################################################################
df = pd.read_csv('./data/rideshare_transit_data.csv')
df = log_transform_time(df)

dropdown_options={
    'rideshareTime': 'Rideshare Trip Time (Minutes)',
    'totalTransitTime': 'Corresponding Transit Trip Time (Minutes)',
    "Log Rideshare Min": "Log of Rideshare Trip Time (Minutes)",
    "Log Transit Min": "Log of Transit Trip Time (Minutes)",
    "Float Trip Miles": "Rideshare Trip Distance (Miles)"
}


# Add controls to build the interaction with dropdown options in intro tab
@callback(
    Output(component_id='altair-hist', component_property='spec'),
    Input(component_id='xaxis-column', component_property='value')
)
def update_graph(row_chosen):
    chart = distribution_of_rides(df, row_chosen, dropdown_options)
    return chart.to_dict()


# Final layout
## App Layout ###
tab_selected_style = {
    'fontWeight': 'bold'
}

app.layout = dcc.Tabs([
    dcc.Tab(
        label='Project Share or Fare', 
        value='main', 
        selected_style=tab_selected_style,
        children=exploratory,
    ),
    dcc.Tab(
        label='1. Comparison of Transit and Rideshare Times',
        value='ratio',
        selected_style=tab_selected_style,
        children=ratio,
    ),
    dcc.Tab(
        label='2. Neighborhood Level Analysis',
        value='neighborhood',
        selected_style=tab_selected_style,
        children=neighborhood_tab,
    ),
    dcc.Tab(
        label='3. Map of Rides',
        value='map',
        selected_style=tab_selected_style,
        children=map_display,
    ),
    dcc.Tab(
        label='4. Discussion',
        value='discussion',
        selected_style=tab_selected_style,
        children=discussion
    ),
    dcc.Tab(
        label='Appendix',
        value='appendix',
        selected_style=tab_selected_style,
        children=appendix,
        width="10%"
    ),
])



# Run the app
if __name__ == '__main__':
    app.run(debug=True)
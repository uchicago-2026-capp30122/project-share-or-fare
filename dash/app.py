from flask import Flask, request, jsonify
import folium
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
from visualization.transform_data import log_transform_time, get_text
from visualization.altair_charts import(
    weighted_avg,
    most_pickups,
    distance_vs_demand_quadrants,
    corridor_bar_chart,
    transit_penalty_heatmap,
    corridor_highest_price,
    corridor_lowest_price,
    distribution_of_rides,
    distribution_of_ratio,
    transit_rideshare_comparison,
    rides_by_month
)


################################################################################
#
# To run the dash app, from base project-share-or-fare directory run
#   `uv run dash/app.py -m`
#
# `ctrl c` to stop running the app.
#
################################################################################


neighborhood_boundaries = pd.read_csv("data/Neighborhoods_2012b_20260227.csv")
neighborhood_route_data = pd.read_csv("data/neighborhood_route_data.csv")

# Get Pickup Neighbhorhood level data and take weighted averages (again)
rides_by_neighborhood  = neighborhood_route_data.groupby(["Pickup Neighborhood","Dropoff Neighborhood"]).apply(
    lambda g: pd.Series({
        'totalTransitTime_wavg': weighted_avg(g, 'totalTransitTime_wavg', 'Count'),
        'rideshareTime_wavg': weighted_avg(g, 'rideshareTime_wavg', 'Count'),
        'tripCost_wavg': weighted_avg(g, "tripCost_wavg", 'Count'),
        'transitPenalty_wavg': weighted_avg(g, "transitPenalty_wavg", 'Count'),
        "distance_wavg": weighted_avg(g, "distance_wavg", "Count"),
        'Count': g['Count'].sum()
    })
    ).reset_index()

server = Flask(__name__)
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.LUX])


current_neighborhood = ""


def standardize(x):
    """
    Standardizes value, used as weighting function for opacity
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
    filtered_neighborhood_routes["opacity"] = standardize(filtered_neighborhood_routes["perc_rides"])

    return filtered_neighborhood_routes


@server.route('/neighborhood', methods=['POST'])
def neighborhood():
    data = request.get_json()
    name = data.get('name')
    # Filter routes dataframe for this neighborhood
    filtered_neighborhood_routes = filter_neighborhood(name)

    # Use only top 5 destinations
    top5_destinations = filtered_neighborhood_routes.sort_values(
        "Count", ascending=False).head(5)

    # Build a GeoJSON FeatureCollection from the matching routes
    features = []
    for _, row in top5_destinations.iterrows():
        pickup_poly = from_wkt(row["Pickup Neighborhood Polygon"])
        dropoff_poly = from_wkt(row["Dropoff Neighborhood Polygon"])
        features.append({
            "type": "Feature",
            "properties": {"line_weight": (row["opacity"]*5)+1,
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
        "name": name,
        "routes": {
            "type": "FeatureCollection",
            "features": features
        }
    })
    

@server.route('/set_neighborhood', methods=['POST'])
def set_neighborhood():
    global current_neighborhood
    current_neighborhood = request.get_json().get('name')
    return jsonify({"status": "ok"})


@server.route('/')
def index():
    m = folium.Map(
        location=(41.86721, -87.63231),
        zoom_control=False,
        tiles="Cartodb Positron",
        zoom_start=11, 
        
    )

    # Build a single GeoJSON FeatureCollection from all neighborhoods
    # This is to plot the neighborhood boundaries
    features = []
    for _, row in neighborhood_boundaries.iterrows():
        geom = from_wkt(row["the_geom"])
        features.append({
            "type": "Feature",
            "properties": {"name": row["PRI_NEIGH"]},
            "geometry": geom.__geo_interface__
        })

    geojson_data = {"type": "FeatureCollection", "features": features}

    # This is what shows the neighborhood name when hovering
    on_each_feature = """
        function test(feature, layer) {
            layer.on('click', function(e) {
                fetch('/neighborhood', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name: feature.properties.name })
                })
                .then(res => res.json())
                .then(data => console.log('Flask response:', data));
            });
        }
    """

    GeoJson(
        geojson_data,
        tooltip=GeoJsonTooltip(fields=["name"], aliases=[""]),
        style_function=lambda f: {'fillOpacity': 0.2, 'weight': 1.5, 'color': '#2a6ebb'},
        highlight_function=lambda f: {'fillOpacity': 0.5},
    ).add_to(m)

    # Inject the click handler JS directly into the map's root HTML
    click_handler_script = f"""
        <script> 
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                {on_each_feature}
                Object.values(window).forEach(function(v) {{
                    if (v && v.eachLayer) {{
                        v.eachLayer(function(layer) {{
                            if (layer.feature) {{
                                var fn = {on_each_feature};
                                fn(layer.feature, layer);
                            }}
                        }});
                    }}
                }});
            }}, 500);
        }});
        </script>
    """

    # Inject custom CSS to remove bounding box
    css = """
        <style>
        * :focus {
            outline: none !important;
            box-shadow: none !important;
            -webkit-tap-highlight-color: transparent !important;
        }

        *:focus-visible {
            outline: none !important;
            box-shadow: none !important;
        }
        </style>
    """



    # Javascript code for mapping route lines when a neighborhood is clicked
    js_code  = """
    <script>
    function styleByFeatureType(feature) {
        return {
            color: feature.properties.color, 
            weight: feature.properties.line_weight,
            opacity: feature.properties.opacity
            };
        } 
    setTimeout(function() {
        const mapObj = Object.values(window).find(v => v instanceof L.Map);

        let currentRoutesLayer = null;

        mapObj.eachLayer(function(layer) {
            console.log("Found layer:", layer);
            
            if (layer.eachLayer) {
                layer.eachLayer(function(sublayer) {
                    console.log("Found sublayer:", sublayer);
                    
                    sublayer.on('click', function(e) {
                        const name = sublayer.feature.properties.name;

                        fetch('/set_neighborhood', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ name: name })
                        });

                        fetch('/neighborhood', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ name: name })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if (currentRoutesLayer) {
                                mapObj.removeLayer(currentRoutesLayer);
                            }
                            currentRoutesLayer = L.geoJSON(data.routes, {
                                style: styleByFeatureType,
                                onEachFeature: function(feature, layer) {
                                    const props = feature.properties;

                                    const tooltipContent = `
                                        <b>From ${props['from']} to ${props['to']}</b><br>
                                        <b>Avg. Transit Time:</b> ${props['transitTime']} min. <br>
                                        <b>Avg. Ride Share Time:</b> ${props['rideshareTime']} min. <br>
                                        <b>% Neighborhood Rides:</b> ${props['perc_rides']}%<br>
                                        <b>Transit/Rideshare Time Ratio: </b> ${props['ratio']}

                                    `;

                                    layer.bindTooltip(tooltipContent, {
                                        sticky: true,      
                                        direction: 'top',
                                        opacity: 0.9,
                                    });

                                    layer.on('mouseover', function(e) {
                                        layer.setStyle({
                                            weight: props.line_weight + 2,
                                            opacity: 1
                                        });
                                    });

                                    layer.on('mouseout', function(e) {
                                        currentRoutesLayer.resetStyle(layer);
                                    });
                                }
                            }).addTo(mapObj);
                        })
                        .catch(err => console.log("Fetch error:", err));
                    });
                });
            }
        });

    }, 1000);
    </script>
    """


    m.get_root().html.add_child(folium.Element(css))
    m.get_root().html.add_child(folium.Element(click_handler_script))
    m.get_root().html.add_child(folium.Element(js_code))
    # m.get_root().html.add_child(folium.Element(css_map_fill))

    html_str = m._repr_html_()

    return html_str


@app.callback(
    Output("panel-title", "children"),
    Output("panel-content", "children"),
    Input("poll-interval", "n_intervals")
)
def update_panel(n):
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
                srcDoc=index(),
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
# Data Processing
df = pd.read_csv('./data/rideshare_transit_data.csv')
df = log_transform_time(df)

dropdown_options={
    'rideshareTime': 'Rideshare Trip Time (Minutes)',
    'totalTransitTime': 'Corresponding Transit Trip Time (Minutes)',
    "Log Rideshare Min": "Log of Rideshare Trip Time (Minutes)",
    "Log Transit Min": "Log of Transit Trip Time (Minutes)",
    "Float Trip Miles": "Rideshare Trip Distance (Miles)"
}

# Load all text
data_text = get_text('dash/text/data.txt')
intro_text = get_text('dash/text/intro.txt')
ratio_intro_text = get_text('dash/text/ratio_intro.txt')
transit_penalty_text = get_text('dash/text/transit_penalty.txt')
discussion_text = get_text('dash/text/discussion.txt')
sampling_text = get_text('dash/text/sampling.txt')
graph_sampling_text = get_text('dash/text/graph_sampling.txt')
seasonal_text = get_text('dash/text/seasonal.txt')


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

## Visualizations ##
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

# Neighborhood Analysis Charts
most_pickups_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=most_pickups(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

distance_vs_demand_quadrants_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=distance_vs_demand_quadrants(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

corridor_bar_chart_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=corridor_bar_chart(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

transit_penalty_heatmap_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=transit_penalty_heatmap(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

corridor_highest_price_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=corridor_highest_price(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

corridor_lowest_price_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=corridor_lowest_price(rides_by_neighborhood).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)

# Seasonality Charts
rides_by_month_chart = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=rides_by_month(df).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"}
)


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

neighborhood = [dbc.Col(children=[
    html.Hr(),
    html.H3("Analysis of Neighborhood Trends"),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.Div([most_pickups_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.Div([distance_vs_demand_quadrants_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.Div([corridor_bar_chart_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.H5(
        "Transit Penalty for Most Frequented Neighborhoods (excl. airports)",
        style={'textAlign': 'center'}),
        html.Div([transit_penalty_heatmap_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.Div([corridor_highest_price_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
    html.Hr(),
    dbc.Row([
        html.Div([corridor_lowest_price_analysis]),
    ]),
    html.Hr(),
    html.Hr(),
], width={"size": 10, "offset": 1})
]


discussion = [dbc.Col(children=[
    html.Hr(),
    html.H3("Discussion of Results"),
    html.Hr(),
    html.Div(
        children=discussion_text,
        style={"white-space": "pre-wrap"}
    )
], width={"size": 10, "offset": 1})]


html.Div(
    children=sampling_text,
    style={"white-space": "pre-wrap"}
)

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
    dbc.Row([
        html.H5(
            "Average Rides per Day by Month",
            style={'textAlign': 'center'}
        ),
        html.Div([rides_by_month_chart]),
    ]),
    html.Hr(),
    html.Hr(),
]

appendix = [html.Div([
    dbc.Row(dbc.Col(
        children=[
            dbc.Stack([
                dbc.Row([
                    html.Hr(),
                    html.Hr(),
                    html.H3("Sampling Methodology"),
                    html.Hr(),
                    html.Div(
                        children=sampling_text,
                        style={"white-space": "pre-wrap"}
                    ),
                    html.Hr()
                ]),
                dbc.Row(graph_sampling),
                dbc.Row(seasonality),
            ], 
            gap = 3)],
        width={"size": 10, "offset": 1},
    )), 
])]

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
        children=neighborhood,
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

# Add controls to build the interaction
@callback(
    Output(component_id='altair-hist', component_property='spec'),
    Input(component_id='xaxis-column', component_property='value')
)
def update_graph(row_chosen):
    chart = distribution_of_rides(df, row_chosen, dropdown_options)
    return chart.to_dict()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
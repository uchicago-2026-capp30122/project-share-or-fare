from flask import Flask, request, jsonify, render_template, render_template_string
import folium
from folium import GeoJson, GeoJsonTooltip, plugins
import pandas as pd
from shapely import from_wkt
import json
import html
from dash import Dash, html, dcc, Output, Input
import numpy as np

neighborhood_boundaries = pd.read_csv("data/Neighborhoods_2012b_20260227.csv")
neighborhood_routes = pd.read_csv("data/neighborhood_route_data.csv")


server = Flask(__name__)
app = Dash(__name__, server=server, url_base_pathname='/dashboard/')


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
    filtered_neighborhood_routes = neighborhood_routes[
        (neighborhood_routes['Pickup Neighborhood'] == neighborhood) &
        (neighborhood_routes['Dropoff Neighborhood'] != neighborhood)
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
        "Count", ascending=False).iloc[:5,:]

    # Build a GeoJSON FeatureCollection from the matching routes
    features = []
    for _, row in top5_destinations.iterrows():
        pickup_poly = from_wkt(row["Pickup Neighborhood Polygon"])
        dropoff_poly = from_wkt(row["Dropoff Neighborhood Polygon"])
        features.append({
            "type": "Feature",
            "properties": {"line_weight": (row["opacity"]*5)+1,
                           "opacity": 1,
                           "color": row["tripDiffRatioColor"],
                           "from": row["Pickup Neighborhood"],
                           "to": row["Dropoff Neighborhood"],
                           "transitTime": round(row["totalTransitTime"],2),
                           "rideshareTime": round(row["rideshareTime"],2),
                           "ratio": round(row["tripDiffRatio"],2),
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

        /* Chrome-specific */
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
        console.log("Map object found:", mapObj);

        let currentRoutesLayer = null;

        mapObj.eachLayer(function(layer) {
            console.log("Found layer:", layer);
            
            if (layer.eachLayer) {
                layer.eachLayer(function(sublayer) {
                    console.log("Found sublayer:", sublayer);
                    
                    sublayer.on('click', function(e) {
                        const name = sublayer.feature.properties.name;
                        console.log("Clicked:", name);

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
                            console.log("Flask returned:", data);
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

                                    // Highlight on hover
                                    layer.on('mouseover', function(e) {
                                        layer.setStyle({
                                            weight: props.line_weight + 2,
                                            opacity: 1
                                        });
                                    });

                                    // Reset on mouseout
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
        np.average(filtered_neighborhood_routes["tripDiffRatio"], 
           weights=filtered_neighborhood_routes["Count"]),
        2))
    
    avg_tripCost = str(round(
        np.average(filtered_neighborhood_routes["Average Trip Total"], 
           weights=filtered_neighborhood_routes["Count"]),
          2)).ljust(5, '0')
    
    

    # get just top 5 destinations
    top5_destinations = filtered_neighborhood_routes.sort_values(
        "Count", ascending=False).iloc[:5,:]
    
    top5 = []
    for i in range(5):
        ngb = top5_destinations[["Dropoff Neighborhood"]].values[i][0]
        perc = top5_destinations[["perc_rides"]].values[i][0]
        ratio = round(top5_destinations[["tripDiffRatio"]].values[i][0],2)
        str_item = f"""{i+1}. {ngb} ({perc}% of rides) """
        top5.append(str_item)

    top5_repr = "\n".join(top5)


    return f"{current_neighborhood}", dcc.Markdown(f"""
**Top 5 destinations:** \n
{top5_repr}

**Transit Penalty Score:** \n {avg_tripDiffRatio} \n

**Average Trip Cost:** \n ${avg_tripCost}
""")


app.layout = html.Div([

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
            "flex": "1"             # ← takes remaining height after header
        }),

        # Footer
        html.P("Sources: Chicago Data Portal (2025) and Google Routes API", style = {"color": "black"})

    ], style={
        "display": "flex",
        "flexDirection": "column",  # ← stack header and map vertically
        "flex": "8",                # ← takes up 80% of page width
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
                    html.Span(" Transit Penalty Score 2 - 2.3")]),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "orange",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 2.3 - 2.7")]),
            html.Div([
                html.Div(None, style={
                        "display":"inline-block",
                        "width": "10px",
                        "height": "10px",
                        "backgroundColor": "red",
                        "border": "solid 1px black"
                    }),
                    html.Span(" Transit Penalty Score 2.7+")]),
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


if __name__ == '__main__':
    app.run(debug=False)
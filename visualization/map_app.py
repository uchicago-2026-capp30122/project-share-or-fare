from flask import Flask, request, jsonify, render_template
import folium
from folium import GeoJson, GeoJsonTooltip, plugins
import pandas as pd
from shapely import from_wkt
import json
import html
from dash import Dash, html, dcc

neighborhood_boundaries = pd.read_csv("data/Neighborhoods_2012b_20260227.csv")
neighborhood_routes = pd.read_csv("data/neighborhood_route_data.csv")

server = Flask(__name__)
app = Dash(__name__, server=server, url_base_pathname='/dashboard/')


@server.route('/neighborhood', methods=['POST'])
def neighborhood():
    data = request.get_json()
    name = data.get('name')
    # Filter routes dataframe for this neighborhood
    filtered_neighborhood_routes = neighborhood_routes[neighborhood_routes['Pickup Neighborhood'] == name]

    # Build a GeoJSON FeatureCollection from the matching routes
    features = []
    for _, row in filtered_neighborhood_routes.iterrows():
        pickup_poly = from_wkt(row["Pickup Neighborhood Polygon"])
        dropoff_poly = from_wkt(row["Dropoff Neighborhood Polygon"])
        features.append({
            "type": "Feature",
            "properties": {"line_weight": 5,
                           "opacity": row["opacity"],
                           "color": row["tripDiffRatioColor"],
                           "from": row["Pickup Neighborhood"],
                           "to": row["Dropoff Neighborhood"],
                           "transitTime": round(row["totalTransitTime"],2),
                           "rideshareTime": round(row["rideshareTime"],2),
                           "n_rides": row["Count"]},
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
    

@server.route('/')
def index():
    m = folium.Map(
        location=(41.86721, -87.63231),
        zoom_control=False,
        tiles="Cartodb Positron",
        zoom_start=11
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

    # JS function that runs for each feature — sends clicked name to Flask
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
            opacity: feature.properties.opacity*5
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
                                        <b>Transit Time:</b> ${props['transitTime']} min. <br>
                                        <b>Ride Share Time:</b> ${props['rideshareTime']} min. <br>
                                        <b>Num. Rides:</b> ${props['n_rides']}
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

    # return m.get_root().render()
    return m._repr_html_()


app.layout = html.Div([
    html.H1("Share or Fare", style={"textAlign": "center"}),

    html.Div([
        html.H2("2025 Ride Share Analysis"),
        html.Iframe(
            id="folium-map",
            srcDoc=index(),
            width="100%",
            height="500px",
            style={"border": "none"}
        )
    ], style={
        "border": "2px solid #ccc",
        "borderRadius": "8px",
        "padding": "10px",
        "margin": "20px",
        "boxShadow": "2px 2px 8px rgba(0,0,0,0.1)"
    }),
])




if __name__ == '__main__':
    app.run(debug=True)
# This defines the CSS styling code and Javascript code to handle displaying 
# the routes when a neighborhood is clicked.

# Inject custom CSS to remove bounding box
CSS_STYLING = """
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

JS_CODE  = """
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
            
            if (layer.eachLayer) {
                layer.eachLayer(function(sublayer) {
                    
                    sublayer.on('click', function(e) {
                        const name = sublayer.feature.properties.name;

                        // Set current neighborhood global, then fetch routes for that neighborhood
                        fetch('/set_neighborhood', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ name: name })
                        }).then(() =>
                            fetch('/neighborhood', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ name: name })
                        }))
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
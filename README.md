# Share or Fare  
### Authors: Molly Long, Waleed Shahzada, Sabrina Wang, Sarah Zebar  

## Abstract 
We analyzed Chicago rideshare trips to understand when, where, and even why residents choose Uber or Lyft over public transportation. We combined rideshare trip data from the City of Chicago Data Portal with hypothetical alternative public transit trips using Google Maps API. Using network-based analysis, we identified common rideshare routes and evaluated whether trips have reasonable public transit alternatives based on travel time, cost, time of day, and neighborhood-level transit access. We assessed whether rideshare usage primarily reflects convenience preferences or unmet transit needs, recognizing that both dynamics likely play a role. We present results through an interactive dashboard that demonstrates answers to our research questions and allows users to explore common trips and compare rideshare and transit options between neighborhoods. Findings may inform CTA service planning and strategies to shift trips toward public transportation. A city with fewer cars on the road and more people using public transporation is a more accessible, more equitable, more sustainable city, and our analysis suggests new routes and essential service improvements towards this goal.  

## Execution
To run the project dashboard:  
*unzip* `neighborhood_route_data.csv.gz`  

*run* `uv run -m dashboard.app`

## Preview 
![App screenshot featuring common rideshare trips that start in Hyde Park](app_preview.png)

## Data Sources
City of Chicago. "Boundaries - Neighborhoods." Chicago Data Portal. Accessed March 1, 2026. https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Neighborhoods/bbvz-uum9.  

City of Chicago. "Transportation Network Providers - Trips (2025-)." Chicago Data Portal. Accessed January 28, 2026. https://data.cityofchicago.org/Transportation/Transportation-Network-Providers-Trips-2025-/6dvr-xwnh/.  

Google. “Routes API.” Google Cloud. https://cloud.google.com/maps-platform/routes.  
# Share or Fare? A Network Analysis of Ride Sharing vs. Transit in Chicago

## Members

- Molly Long (mrlong@uchicago.edu)
- Sabrina Wang (sabrinawang@uchicago.edu)
- Sarah Zebar (szebar@uchicago.edu)
- Waleed Shahzad (waleedks@uchicago.edu)

## Abstract

We plan to analyze Chicago rideshare trips to understand when, where, and perhaps why riders choose Uber or Lyft over public transportation. We will combine rideshare trip data from the City of Chicago Data Portal with CTA route, service, and real-time data, reconciling these sources at the neighborhood and census tract level. Using network-based analysis, we will identify common rideshare routes and evaluate whether trips have reasonable public transit alternatives based on travel time, cost, time of day, and neighborhood-level transit access. We will assess whether rideshare usage primarily reflects convenience preferences among higher-income riders or unmet transit needs, recognizing that both dynamics likely play a role. We might potentially incorporate Census data to contextualize trips using neighborhood demographics. Results will be presented through an interactive dashboard that demonstrates answers to our research questions and allows users to explore common trips and compare rideshare and transit options, including differences in price, duration, and estimated emissions. Findings may inform CTA service planning and strategies to shift trips toward public transportation.

## Preliminary Data Sources

### Data Source #1
Source URL: https://data.cityofchicago.org/Transportation/Transportation-Network-Providers-Trips-2025-/6dvr-xwnh/data_preview

Source Type: CSV Export OR API

Summary: 2025-Current trip-level data reported by Transportation Network Providers (i.e. Lyft/Uber) in Chicago from the Chicago Data Portal

Challenges: There are 85.8M rows... we'll definitely need to do some filtering based on one of the fields.

### Data Source #2
Source URL: https://transitapp.com/partners/apis

Source Type: API

Summary: Data on routes for getting from Point A to B using public transportation - i.e. modes of transport, total trip time, etc.

Challenges: We want to match the coordinates for each trip start and end point (from Data Source #1) with attributes of the public-transit-only alternative, so we'll probably need to do some pre-processing so that the coordinate data types are compatible. Another challenge - this only gives real-time data, but ideally we would want route information at the same time as the corresponding trip. 

## Questions

1. The query limit for the transit API is five API calls per minute and 1,500 API calls per month. Will that be enough?
2. Could we potentially use the Google Maps API? It looks like it costs money but maybe there's a workaround. 

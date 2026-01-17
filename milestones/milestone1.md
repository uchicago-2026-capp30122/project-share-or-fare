# Share or Fare? A Network Analysis of Ride Sharing vs. Transit in Chicago

## Members

- Molly Long (mrlong@uchicago.edu)
- Sabrina Wang (sabrinawang@uchicago.edu)
- Sarah Zebar (szebar@uchicago.edu)
- Waleed Shahzad (waleedks@uchicago.edu)

## Abstract

100-200 words explaining the general idea for your project.  Be sure to read the project requirements below and consider how you'll incorporate the various components.

*These details can & will change as much as needed over the next few weeks.*

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

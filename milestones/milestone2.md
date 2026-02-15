# Share or Fare

## Abstract

We plan to analyze Chicago rideshare trips to understand when, where, and perhaps why riders choose Uber or Lyft over public transportation. We will combine rideshare trip data from the City of Chicago Data Portal with CTA route, service, and real-time data, reconciling these sources at the neighborhood and census tract level. Using network-based analysis, we will identify common rideshare routes and evaluate whether trips have reasonable public transit alternatives based on travel time, cost, time of day, and neighborhood-level transit access. We will assess whether rideshare usage primarily reflects convenience preferences among higher-income riders or unmet transit needs, recognizing that both dynamics likely play a role. We might potentially incorporate Census data to contextualize trips using neighborhood demographics. Results will be presented through an interactive dashboard that demonstrates answers to our research questions and allows users to explore common trips and compare rideshare and transit options, including differences in price, duration, and estimated emissions. Findings may inform CTA service planning and strategies to shift trips toward public transportation.

## Data Sources

### Data Source #1

Source URL: {https://data.cityofchicago.org/Transportation/Transportation-Network-Providers-Trips-2025-/6dvr-xwnh/about_data}
Source Type: Bulk data
Approximate Number of Records (rows): 93.5M
Approximate Number of Attributes (columns): 24
Current Status: Molly and Sabrina have downloaded the dataset and have done some exploratory filtration in a Jupyter notebook. We are explorint different ways to make the dataset scope smaller and the resolution courser so the dataset is easier to work with, including clutering rides by location and time such that the smallest resolution in the dataset is about 100 meteres and one hour, not .000001 lat/long and 1 second. Next, we will create a toy dataset with about 100 entries to work on other pieces of the project while concurrently finalizing the rows we want to work with.
Challenges: The dataset is massive, so operations are slow. Additionally, Sabrina's starting csv is different than Molly's (they applied different filters from the source website), but after data cleaning using pandas, the datasets still have different numbers of rows even through the same filters have been applied to both. We're working on exploring the differences between the datasets to make sure we understand the data we are working with.

### Data Source #2
Source URL: (https://routes.googleapis.com/directions/v2:computeRoutes)
Source Type: API
Approximate Number of Records (rows): The query limit is about 240,000. 
Approximate Number of Attributes (columns): 5 (ish)
Current Status: Mostly finished the code for pulling the relevant data from the API. Wrote a function for computing the JSON headers and data for the HTTP request based on our inputs, and one for actually calling the API and caching the results.
Challenges: I need to make sure that I'm not pushing the API key to Github, so I (Sarah) think I'll set up a meeting with James before I actually push the code to make sure everything looks good. 


## Data Reconciliation Plan

In order to pare down the number of observations, we will group rides by hour, approximate pick-up location and approximate drop-off location. For each hour/pick-up/drop-off strata, we will call the Google API using those inputs to obtain several fields relating to the corresponding public transit trip such as duration, distance, number of transfers, and total cost. In this way, the unique key is the combination of hour of day and the latitude and longitude pairs representing the two locations. 


## Project Plan

By the end of Week 4:
- Molly and Sabrina: Download Rideshare data, identify intial geographic and time scope, explore clustering observations by time and pick-up/drop-off locations
- Waleed and Sarah: Work on the code for accessing the Google API

By the end of Week 5:
- Molly and Sabrina: Solidify scope of dataset and filter observations - have a finalized dataset of all observations we're interested in. Pull 1,000 random observations as a "toy dataset" for testing. 
- Sarah and Waleed: Solidify the variables we're interested in and make a sucessful API call

By the end of Week 6: 
- Sarah and Sabrina: Merge datasets and think about key insights we want to show/visualize.
- Molly and Waleed: Research network analysis packages
- All: discuss specifics of what the final result will look like. 

By the end of Week 7:
- ???: Begin constructing the final visualization (probably a network map) 
- ???: If we have time: Look into merging in census tract data (understand factors such as income/profession, neighbourhoods etc. of people who prefer rideshare)

Our prototype will ideally be an interactive map using the toy dataset that shows common ride share routes in Chicago and the alternate transit route, and a cost/duration/distance comparison. 

By the end of Week 8:
- All: Recreate the map and other visualizations with the full dataset.
- ???: Add any additional charts and analysis we're interested in. 

By the end of Week 9:
- Finishing touches

The final goal of this milestone is to develop a team plan that will keep you on track for the remainder of the quarter.

1. Identify the key components of your project based on the criteria and your intended end result. (e.g. "Web scrape data source #1", "Merge code for Data Sources #2 and #3", "Map-based visualization")
2. For each component identify who will be responsible, and when it should be ready. Consider if any components rely on others and how to mitigate the effect on the dependent team members (e.g. mock data for the visualization until the real data is ready)
3. Put this together into a (rough) weekly plan. What will be built by Week 7's prototype? 

## Questions

1. The Google API returns a polyline object that I *think* we could use to overlay the transit route on a map. Do you know of any resources to learn about this? Or resources about mapping/GIS in general. 
2. We will be dealing with a lot of data. What is the best way to store and share this data and the cache files using Github? Should we commit the entire dataset to Github and pull it each time, or should we each have a copy on our local computer that we refer to?

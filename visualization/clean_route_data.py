# clean_route_data.py
# This file loads in ride-group-level data with the api responses, merges it with
# neighborhood boundaries and polyogn data

import folium
from folium import plugins
import webbrowser
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely import from_wkt
import shapely.wkt

# Define column names for convenience
PICKUP_LAT = "Pickup Centroid Latitude"
PICKUP_LONG = "Pickup Centroid Longitude"
DROPOFF_LAT = "Dropoff Centroid Latitude"
DROPOFF_LONG = "Dropoff Centroid Longitude"


def standardize(x):
    """
    Standardizes value, used as weighting function for opacity/size
    """
    return (x-x.min())/(x.max()-x.min())



def clean_route_data(route_data):
    # convert totalTime field to minutes 
    route_data["totalTime"] = route_data["totalTime"].apply(lambda s: int(str(s)[:-1]))/60
    print("here")
    # convert ride share time to minutes
    route_data["Average Trip Minutes"] = route_data["Average Trip Seconds"]/60

    route_data = route_data.rename(columns={
        "totalTime": "totalTransitTime",
        "Average Trip Minutes": "rideshareTime"
    })


    # Aggregate route data by day type and hour to get pickup, dropoff level data
    # Take average of transit time, ride share time, and sum of trip count
    route_data = route_data.groupby([PICKUP_LAT, PICKUP_LONG, DROPOFF_LAT, DROPOFF_LONG]).agg({
    "totalTransitTime" : "mean",
    "rideshareTime" : "mean",
    "Count": "sum"
    }).reset_index()
    
    return route_data


def join_neighborhood_data(route_data, neighborhood_boundaries):
    # Initialize new columns
    route_data["Pickup Neighborhood"] = ""
    route_data["Pickup Neighborhood Polygon"] = ""
    route_data["Dropoff Neighborhood"] = ""
    route_data["Dropoff Neighborhood Polygon"] = ""

    ## Join ride group and neighborhood data
    # Loop over route data rows
    for i, ride_group in route_data.iterrows():
        pickup_point = Point(ride_group[PICKUP_LONG], ride_group[PICKUP_LAT])
        dropoff_point = Point(ride_group[DROPOFF_LONG], ride_group[DROPOFF_LAT])

        # Loop over neighborhood dataset
        # If pickup_point or drop_off point in neighborhood polygon,
        # add to route data frame
        for _, neighborhood in neighborhood_boundaries.iterrows():
            neighborhood_polygon = from_wkt(neighborhood["the_geom"])
            if neighborhood_polygon.contains(pickup_point):
                route_data.loc[i, "Pickup Neighborhood"] = neighborhood["PRI_NEIGH"]
                route_data.loc[i, "Pickup Neighborhood Polygon"] = neighborhood["the_geom"]
            if neighborhood_polygon.contains(dropoff_point):
                route_data.loc[i, "Dropoff Neighborhood"] = neighborhood["PRI_NEIGH"]
                route_data.loc[i, "Dropoff Neighborhood Polygon"] = neighborhood["the_geom"]

    # Aggregate points by pickup and dropoff neighborhood
    # Take average transit time and rideshare time, sum of count
    agg_route_data = route_data.groupby(["Pickup Neighborhood", "Pickup Neighborhood Polygon",
                    "Dropoff Neighborhood", "Dropoff Neighborhood Polygon"])[[
                        "transitTime",
                        "rideshareTime",
                        "Count"
                    ]].agg({
                        "totalTransitTime" : "mean",
                        "rideshareTime" : "mean",
                        "Count": "sum"  
                    }).reset_index()
    
    # Filter out missing values *** To Do: look into why there are missing values
    agg_route_data=agg_route_data[(agg_route_data["Dropoff Neighborhood Polygon"] != "") &
               (agg_route_data["Pickup Neighborhood Polygon"] != "")]
    
    
    return agg_route_data

def aes_mapping(data):
    """
    Add trip diff variable and attributes for line weight, 
    opacity, and color
    """

    # Add tripDiffTime and color mapping
    data["tripDiffTime"] = data["totalTransitTime"] - data["rideshareTime"]
    bins = [0, 0.25, 0.50, 0.75, 1]
    labels = ["green", "yellow", "orange", "red"]
    data["tripDiffTimeColor"] = pd.cut(data["tripDiffTime"].rank(pct=True), bins=bins, labels=labels)

    # Add line weight and opacity
    data["line_weight"] = (standardize(data['Count']) + 0.1) * 5
    data["opacity"] = (standardize(data['Count']) + 0.1)    

    return data



def main():
    # Load in route data and clean
    route_data = pd.read_csv("data/small_medium_merged.csv", sep=",").dropna()
    cleaned_route_data = clean_route_data(route_data)
    print("Route Data Cleaned")

    # Load in neighborhood GIS data and join with route data
    neighborhood_boundaries = pd.read_csv("data/Neighborhoods_2012b_20260227.csv", sep=",")
    joined_data = join_neighborhood_data(cleaned_route_data, neighborhood_boundaries)
    print("Join completed")

    final_data = aes_mapping(joined_data)

    # Output final dataset
    final_data.to_csv("data/neighborhood_route_data.csv")



main()


# clean_route_data.py
# Takes in small_medium_merged_neighborhood.csv  data, and:
#  - aggregates to the pickup/dropoff neighborhood level
#  - adds pickup/dropoff neighborhood polygons
#  - adds "connectivity measure" (transitTime/rideshareTime)
#  - adds color based on connectivity measure and line opacity based on count

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
    """
    Cleans and renames time fields, aggregates by Pickup and Dropoff neighborhood
    """
    # convert totalTime field to minutes 
    route_data["totalTime"] = route_data["totalTime"].apply(lambda s: int(str(s)[:-1]))/60

    # convert ride share time to minutes
    route_data["Average Trip Minutes"] = route_data["Average Trip Seconds"]/60

    route_data = route_data.rename(columns={
        "totalTime": "totalTransitTime",
        "Average Trip Minutes": "rideshareTime"
    })

    # Aggregate route by pickup and dropoff neighborhood
    route_data = route_data.groupby(["Pickup Neighborhood", "Dropoff Neighborhood"]).agg({
    "totalTransitTime" : "mean",
    "rideshareTime" : "mean",
    "Count": "sum",
    "Average Trip Total": "mean"
    }).reset_index()
    
    return route_data


def join_neighborhood_data(route_data, neighborhood_boundaries):
    """
    Merge in polygon data
    """

    # Pickup neighborhood
    route_data = route_data.merge(neighborhood_boundaries[["the_geom", "PRI_NEIGH"]], 
                     left_on = "Pickup Neighborhood",
                     right_on = "PRI_NEIGH",
                     how = "left")
    route_data = route_data.rename(columns = {"the_geom": "Pickup Neighborhood Polygon"})

    # Dropoff neighborhood
    route_data = route_data.merge(neighborhood_boundaries[["the_geom", "PRI_NEIGH"]], 
                     left_on = "Dropoff Neighborhood",
                     right_on = "PRI_NEIGH",
                     how = "left")
    route_data = route_data.rename(columns = {"the_geom": "Dropoff Neighborhood Polygon"})


    # Filter out missing values *** To Do: look into why there are missing values
    route_data=route_data[(route_data["Dropoff Neighborhood Polygon"] != "") &
               (route_data["Pickup Neighborhood Polygon"] != "")]
    
    
    return route_data

def aes_mapping(data):
    """
    Add trip diff variable and attributes for line weight, 
    opacity, and color
    """

    # Add tripDiffRatio and color mapping
    data["tripDiffRatio"] = data["totalTransitTime"]/data["rideshareTime"]
    bins = [0, 0.25, 0.50, 0.75, 1]
    labels = ["green", "yellow", "orange", "red"]
    data["tripDiffRatioColor"] = pd.cut(data["tripDiffRatio"].rank(pct=True), bins=bins, labels=labels)

    # Add  and opacity
    # data["opacity"] = (standardize(data['Count']) + 0.1)    

    return data



def main():
    # Load in route data, clean and aggregate
    route_data = pd.read_csv("data/small_medium_merged_neighborhood.csv", sep=",").dropna()
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


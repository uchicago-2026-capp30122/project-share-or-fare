import pandas as pd
from shapely.geometry import Point
from shapely import from_wkt

# Define column names for convenience
PICKUP_LAT = "Pickup Centroid Latitude"
PICKUP_LONG = "Pickup Centroid Longitude"
DROPOFF_LAT = "Dropoff Centroid Latitude"
DROPOFF_LONG = "Dropoff Centroid Longitude"

def join_api_csv(rideshare_data_name, large = False) -> pd.DataFrame:
    """
    Join the output csv from the api call back to the original csv dataset on group_id

    Parameters:
        rideshare_data_name: A string, the name of the original rideshare data
        api_response_name: A string, the name of the api response file
    
    Returns: A pandas dataframe with the merged rideshare and transit data

    Author: Sabrina
    """
    transit_dataset_names = [
        "molly_10k_api_response",
        "sabrina_10k_api_response",
        "sarah_10k_api_response",
        "waleed_10k_api_response",
        "molly_500_api_response",
        "sabrina_500_api_response",
        "sarah_500_api_response",
        "waleed_500_api_response"
    ]

    if large:
        transit_dataset_names = [
            "molly_58k_api_response",
            "sabrina_58k_api_response",
            "sarah_58k_api_response",
            "waleed_58k_api_response"
        ]

    transit_datasets = []
    for name in transit_dataset_names:
        df = pd.read_csv(f"./data/{name}.csv")
        transit_datasets.append(df)
    
    transit_data = pd.concat(transit_datasets, axis=0)
    rideshare_data = pd.read_csv(f"./data/{rideshare_data_name}.csv")

    # Perform a join to get all rideshare data that has a matching transit call
    #   Left join with transit on the left, rideshare on the right.
    #   Transit primary key: group_id to rideshare foreign key: group_id
    #   Effectivley we are getting all rides for which we have a transit
    #   api call for.
    rideshare_transit_data = rideshare_data.merge(
        transit_data,
        on="group_id",
        how="inner"
    )
    return rideshare_transit_data


def join_neighborhood_data(route_data, neighborhood_boundaries):
    """
    This function merges in "Pickup Neighborhood" and "Dropoff 
    Neighborhood" columns.
    """
    # Initialize new columns
    route_data["Pickup Neighborhood"] = ""
    route_data["Dropoff Neighborhood"] = ""

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
            if neighborhood_polygon.contains(dropoff_point):
                route_data.loc[i, "Dropoff Neighborhood"] = neighborhood["PRI_NEIGH"]

    return route_data

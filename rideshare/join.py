import pandas as pd

def join_api_csv(rideshare_data_name, api_response_name) -> pd.DataFrame:
    """
    Join the output csv from the api call back to the original csv dataset on group_id

    Parameters:
        rideshare_data_name: A string, the name of the original rideshare data
        api_response_name: A string, the name of the api response file
    
    Returns: A pandas dataframe with the merged rideshare and transit data

    Author: Sabrina
    """
    rideshare_data = pd.read_csv(f"./data/{rideshare_data_name}.csv")
    transit_data = pd.read_csv(f"./data/{api_response_name}.csv")

    # Perform a join to get all rideshare data that has a matching transit call
    #   Left join with transit on the left, rideshare on the right.
    #   Transit primary key: group_id to rideshare foreign key: group_id
    #   Effectivley we are getting all rides for which we have a tranist
    #   api call for.
    rideshare_transit_data = pd.merge(transit_data, rideshare_data, on='group_id', how='left')

    return rideshare_transit_data

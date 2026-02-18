import pandas as pd

def join_api_csv(rideshare_data_name, api_response_name) -> pd.DataFrame:
    """
    Join the output csv from the api call back to the original csv dataset on group_id

    Parameters:
        rideshare_data_name: A string, the name of the original rideshare data
        api_response_name: A string, the name of the api response file
    
    Returns: A pandas dataframe with the merged rideshare and transit data
    """
    rideshare_data = pd.read_csv(f"./data/{rideshare_data_name}.csv")
    transit_data = pd.read_csv(f"./data/{api_response_name}.csv")

    rideshare_transit_data = pd.merge(rideshare_data, transit_data, on='group_id', how='left')

    return rideshare_transit_data

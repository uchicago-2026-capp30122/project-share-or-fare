import pandas as pd

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

    # Set the index column before running pd.join (faster than pd.merge)
    transit_data.set_index("group_id", inplace=True)
    rideshare_data.set_index("group_id", inplace=True)

    # Perform a join to get all rideshare data that has a matching transit call
    #   Left join with transit on the left, rideshare on the right.
    #   Transit primary key: group_id to rideshare foreign key: group_id
    #   Effectivley we are getting all rides for which we have a tranist
    #   api call for.
    rideshare_transit_data = transit_data.join(rideshare_data, how='left')

    return rideshare_transit_data

import pandas as pd


def join_api_csv(rideshare_data_name, api_response_name):
    """
    Join the output csv from the api call back to the original csv dataset on group_id
    """
    r = f"./data/{rideshare_data_name}.csv"
    print(r)
    rideshare_data = pd.read_csv(r)
    transit_data = pd.read_csv(f"./data/{api_response_name}.csv")

    rideshare_transit_data = pd.merge(
        rideshare_data, transit_data, on="group_id", how="left"
    )

    return rideshare_transit_data

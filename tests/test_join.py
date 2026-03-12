import os

import pandas as pd
import pytest

# these tests analyze output files


def test_join_output():
    # define paths to existing files
    rideshare_path = "data/molly_10k.csv"
    api_path = "data/molly_10k_api_response.csv"
    merged_path = "data/rideshare_transit_data.csv"

    # read in files to check
    rideshare_df = pd.read_csv(rideshare_path)
    api_df = pd.read_csv(api_path)
    merged_df = pd.read_csv(merged_path)

    # expected subset
    molly_rideshare_ids = set(rideshare_df["group_id"])
    molly_api_ids = set(api_df["group_id"])
    molly_joint_ids = molly_rideshare_ids.intersection(molly_api_ids)

    # check data consitency for a random group to make sure miles match
    sample_id = list(molly_joint_ids)[0]

    # get pickup location from the input and the output
    expected_long = rideshare_df[rideshare_df["group_id"] == sample_id][
        "Pickup Centroid Longitude"
    ].iloc[0]
    actual_long = merged_df[merged_df["group_id"] == sample_id][
        "Pickup Centroid Longitude"
    ].iloc[0]

    assert expected_long == actual_long, f"Location mismatch for ID {sample_id}"

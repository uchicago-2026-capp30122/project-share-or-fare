import numpy as np
import pandas as pd
import matplotlib
import datetime as dt
from zoneinfo import ZoneInfo

# Update random state before running
SAMPLED = []
RANDOM_STATE = 11
TEAMMATES = ["molly", "sabrina", "sarah", "waleed"]


def clean(filename: str) -> pd.DataFrame:
    """
    Basic cleaning the raw. Takes around 15 minutes to run.
    Cleaning:
        - Only trips with all fields not NA
        - Only trips 100% in Chicago
        - Format pickup and dropoff time as a timestamp

    Parameters:
        filename: The string for the path to the csv downloaded from Chicago
            Data Portal

    Returns: A pandas DataFrame with the cleaned data

    Author: Molly
    """
    df = pd.read_csv(filename, dtype={"Trip Miles": float})

    # Select relevant columns
    data = df[
        [
            "Trip ID",
            "Trip Start Timestamp",
            "Trip End Timestamp",
            "Trip Seconds",
            "Trip Miles",
            "Percent Time Chicago",
            "Percent Distance Chicago",
            "Pickup Census Tract",
            "Dropoff Census Tract",
            "Fare",
            "Tip",
            "Additional Charges",
            "Trip Total",
            "Pickup Centroid Latitude",
            "Pickup Centroid Longitude",
            "Dropoff Centroid Latitude",
            "Dropoff Centroid Longitude",
        ]
    ]

    # Drop all NAs
    data = data.replace("NaN", np.nan)
    data = data.dropna()

    # Filter to only include trips 100% in Chicago
    data["Int Percent Time Chicago"] = (
        data["Percent Time Chicago"].str.replace("%", "").str.replace(",", "")
    ).astype(int)

    data["Int Percent Distance Chicago"] = (
        data["Percent Distance Chicago"].str.replace("%", "").str.replace(",", "")
    ).astype(int)

    data = data[
        (data["Int Percent Time Chicago"] == 100)
        & (data["Int Percent Distance Chicago"] == 100)
    ]

    # Convert timestamp fields to datetime format, specify Chicago time zone,
    # convert to UTC (correct time zone for API).
    # If timestamp is ambiguous due to the daylight savings time
    # change, drop from dataset.
    data["Trip Start Timestamp"] = (
        pd.to_datetime(data["Trip Start Timestamp"], format="%m/%d/%Y %I:%M:%S %p")
        .dt.tz_localize("America/Chicago", ambiguous="NaT", nonexistent="NaT")
        .dt.tz_convert("UTC")
    )

    data["Trip End Timestamp"] = (
        pd.to_datetime(data["Trip End Timestamp"], format="%m/%d/%Y %I:%M:%S %p")
        .dt.tz_localize("America/Chicago", ambiguous="NaT", nonexistent="NaT")
        .dt.tz_convert("UTC")
    )

    data = data.dropna(subset=["Trip Start Timestamp", "Trip End Timestamp"])

    # Specify boundaries in UTC
    start_ct = pd.Timestamp("2025-01-01 00:00:00", tz="America/Chicago")
    end_ct = pd.Timestamp("2025-12-31 23:59:59", tz="America/Chicago")

    start_utc = start_ct.tz_convert("UTC")
    end_utc = end_ct.tz_convert("UTC")

    data = data[
        (data["Trip Start Timestamp"] >= start_utc)
        & (data["Trip End Timestamp"] <= end_utc)
    ]

    print(f"Cleaned data has {len(data)} rows")
    return data


def group_rides(data: pd.DataFrame) -> pd.DataFrame:
    """
    Grouping by Unique API Call

    We have a limited number of API calls and want to use them efficiently.
    Rather than making repeated calls that return identical results, we will
    consolidate requests whenever possible.

    Under our working assumptions--including that CTA schedules remain constant
    over the sample period (and match current schedule), that we ignore traffic
    variation, and that all weekdays are treated as equivalent—we will make one
    API call per unique set of parameters and apply the returned transit
    information to all rideshare trips that share those parameters.

    Specifically, if multiple rideshare trips share the same:
        - Start and end coordinates (rounded to three decimal places)
        - Day type (0 = weekday, 1 = Saturday, 2 = Sunday)
        - Start hour
    then a single API call will suffice for all of them.

    To implement this, we will:
    1. Create a dataframe that counts the number of trips in each group
    defined by the criteria above.
    2. Take a weighted random sample from this grouped dataframe.
    3. This is the sample that we will pass to the API program.

    This approach allows us to maximize sample size from the rideshare dataset
    (which is population data) while minimizing API usage.

    Author: Molly
    """
    # round coodinates to 3 decimal points (~111m)
    cols = [
        "Pickup Centroid Latitude",
        "Pickup Centroid Longitude",
        "Dropoff Centroid Latitude",
        "Dropoff Centroid Longitude",
    ]

    data[cols] = data[cols].round(3)

    # extract start hour
    data["start_hour"] = data["Trip Start Timestamp"].dt.hour

    # create day type variable
    wd = data["Trip Start Timestamp"].dt.weekday
    data["day_type"] = (wd == 5).astype(int) + (wd == 6).astype(int) * 2

    # group on selected columns
    group_cols = [
        "day_type",
        "start_hour",
        "Pickup Centroid Latitude",
        "Pickup Centroid Longitude",
        "Dropoff Centroid Latitude",
        "Dropoff Centroid Longitude",
    ]

    unique_calls = data.groupby(group_cols).size().reset_index(name="group_n")

    # create group id for each unique call
    unique_calls["group_id"] = unique_calls.index

    # merge group id back into full dataset for later matching purposes
    data = data.merge(
        unique_calls[group_cols + ["group_id"]], on=group_cols, how="left"
    )

    print(f"Length of full dataset: {len(data)}")
    print(f"Number of unique API calls: {len(unique_calls)}")
    return unique_calls


def write_month_ride_groups(data: pd.DataFrame):
    """
    Creates dataframe of unique rides-and-month, and writes that to the
    `ride_groups` csv file.

    Parameters:
        data: A pandas dataframe of cleaned but not grouped ride data

    Authors: Sabrina, Molly
    """
    # `data` as is defined under the grouping data section
    # Trip length as an int
    data["Int Trip Seconds"] = data["Trip Seconds"].str.replace(",", "").astype(int)

    # Turn all money into floats
    col_name = ["Fare", "Tip", "Additional Charges", "Trip Total"]
    for col in col_name:
        data[f"Float {col}"] = data[col].str[1:].astype(float)

    # Trip miles as a float
    data["Float Trip Miles"] = data["Trip Miles"].astype(float)

    # Convert time variables to Central time
    data["Trip Start Timestamp"] = data["Trip Start Timestamp"].dt.tz_convert(
        "America/Chicago"
    )
    data["Trip End Timestamp"] = data["Trip End Timestamp"].dt.tz_convert(
        "America/Chicago"
    )

    # Recreate time variables in proper time zone
    data["month"] = data["Trip Start Timestamp"].dt.month
    data["start_hour"] = data["Trip Start Timestamp"].dt.hour

    ride_groups = (
        data.groupby(["group_id", "month"])
        .aggregate(
            {
                "Int Trip Seconds": "mean",
                "Float Trip Miles": "mean",
                "Float Fare": "mean",
                "Float Tip": "mean",
                "Float Additional Charges": "mean",
                "Float Trip Total": "mean",
                "Pickup Census Tract": "first",
                "Dropoff Census Tract": "first",
                "Pickup Centroid Latitude": "first",
                "Pickup Centroid Longitude": "first",
                "Dropoff Centroid Latitude": "first",
                "Dropoff Centroid Longitude": "first",
                "start_hour": "first",
                "day_type": "first",
                "Trip ID": "count",
            }
        )
        .reset_index()
    )

    ride_groups = ride_groups.rename(
        columns={
            "Int Trip Seconds": "Average Trip Seconds",
            "Trip Miles": "Average Miles",
            "Float Fare": "Average Fare",
            "Float Tip": "Average Tip",
            "Float Additional Charges": "Average Additional Charges",
            "Float Trip Total": "Average Trip Total",
            "Trip ID": "Count",
        }
    )

    print(f"Agregated data has {len(ride_groups)} rows")
    ride_groups.to_csv("../data/ride_groups.csv", index=False)
    print("Sucessfully wrote ride_group dataset to data/ride_groups.csv")


def format_for_api(data: pd.DataFrame, unique_calls: pd.DataFrame) -> pd.DataFrame:
    """
    Convert day types into specific representative dates, with separate year,
    month, and day columns with data as strings.

    Parameters:
        data
        unique_calls

    Returns: A pandas DataFrame with unique calls and with year, month, and day
    values formatted for the API call

    Author: Molly
    """
    unique_calls["representative_year"] = "2026"
    unique_calls["representative_month"] = "04"
    unique_calls["representative_day"] = data["day_type"].map({0: 22, 1: 25, 2: 26})

    return unique_calls


def sample_and_split(data: pd.DataFrame, size: int):
    """
    Draws a sample from our dataset and stores it into 4 separate CSV files.
    Each csv has size number of rows

    Parameters:
        data: pandas DataFrame
        size: int, 1/4 sample size to take

    Writes 4 csv files

    Author: Molly
    """
    # update dataset to avoid repeat pulls
    # data_for_api_58k = data_for_api_10k[
    #     ~data_for_api_10k["group_id"].isin(api_10k["group_id"])
    # ]

    # Sample size * 4 calls, weighting likelihood of being sampled by group size
    api = data.sample(
        size * 4, weights="group_n", replace=True, random_state=RANDOM_STATE
    )

    for i, teammate in enumerate(TEAMMATES):
        selected_data = api[size * i : size * (i + 1)]
        selected_data.to_csv(f"./data/{teammate}_{size / 1000}k.csv", index=False)

    print(f"Succesfully created files of size {size}")

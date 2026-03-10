import pandas as pd
import random
import math


def log_transform_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates columns for log trip time in the given dataframe

    Arguments:
        df: A pandas dataframe

    Returns: A pandas dataframe with additional columns log of ridshare time
        and log of transit time

    Author: Sabrina
    """
    df["Log Rideshare Min"] = (df["rideshareTime"]).apply(math.log10)
    df["Log Transit Min"] = (df["totalTransitTime"]).apply(math.log10)

    df["Log Rideshare Min"] = (df["Log Rideshare Min"]).apply(
        lambda x: math.trunc(x * 10) / 10
    )

    df["Log Transit Min"] = (df["Log Transit Min"]).apply(
        lambda x: math.trunc(x * 10) / 10
    )

    return df


def dataset_sample(df: pd.DataFrame, fraction: int) -> pd.DataFrame:
    """
    Takes a sample of roughly 1/fraction of the dataset. Assumes that the last
    digits of the trip length in seconds is random and independent from any
    relevant factors.

    Arguments:
        df: A pandas data frame
        fraction: inverse of sample size

    Returns: A smaller semi-random sample of the dataframe

    Author: Sabrina
    """
    random_number = random.randint(0, fraction - 1)

    df = df[(df["rideshareTime"] < 100) & (df["totalTransitTime"] < 100)]
    df = df[df["Average Trip Seconds"] % fraction == random_number]

    return df


def weighted_median(df: pd.DataFrame, col: str) -> float:
    """
    Gets the weighted median for the given col

    Arguments:
        df: A pandas dataframe

    Returns: A float, the median, weighted by number of rides (the `Count` col)

    Author: Sabrina
    """
    df_sorted = df.sort_values(col)
    cumsum = df_sorted["Count"].cumsum()
    cutoff = df_sorted["Count"].sum() / 2
    median = df_sorted[cumsum >= cutoff][col].iloc[0]

    return median


def get_text(filepath: str) -> str:
    """
    Loads the text in a file as a string variable

    Arguments:
        filepath: The filepath to a .txt file

    Returns: A string, the content of the text file

    Author: Sabrina
    """
    try:
        with open(filepath, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Could not find file `{filepath}`")
        return ""

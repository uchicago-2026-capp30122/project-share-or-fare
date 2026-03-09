"""
Description:
    This file contains the functions to load our combined dataset and
    apply any transformations needed for visualizations
"""
import pandas as pd
import random
import math


def log_transform_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Author: Sabrina
    """
    df["Log Rideshare Min"] = (df['rideshareTime']).apply(math.log10)
    df["Log Transit Min"] = (df['totalTransitTime']).apply(math.log10)

    df["Log Rideshare Min"] = (df["Log Rideshare Min"]).apply(
        lambda x: math.trunc(x * 10) / 10
    )

    df["Log Transit Min"] = (df["Log Transit Min"]).apply(
        lambda x: math.trunc(x * 100) / 100
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


def get_text(filepath: str) -> str:
    """
    
    Author: Sabrina
    """
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print("BAD FILE PATH")
        return ""
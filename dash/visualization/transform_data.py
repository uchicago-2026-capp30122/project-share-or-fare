"""
Description:
    This file contains the functions to load our combined dataset and
    apply any transformations needed for visualizations
"""

import pandas as pd
import numpy as np
import altair as alt
import random
import math


def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Author: Sabrina
    """
    df = df.replace("NaN", np.nan)
    df = df.dropna()

    df["totalTime"] = df["totalTime"].str[:-1]
    df["totalTime"] = df["totalTime"].astype('Int64')
    df["totalTimeMin"] = df["totalTime"] / 60
    df["Average Trip Minutes"] = df["Average Trip Seconds"] / 60

    df["Number of Modes"] = df["modes"].str.split(",").apply(len)

    df["Transit Percentage Longer"] = ((df["totalTimeMin"] - df["Average Trip Minutes"]) / df["Average Trip Minutes"]).round(1)
    df["Transit Rideshare Ratio"] = (df["totalTimeMin"] / df["Average Trip Minutes"]).round(1)

    df["Log Rideshare Min"] = (df['Average Trip Minutes']).apply(math.log10)
    df["Log Transit Min"] = (df['totalTimeMin']).apply(math.log10)

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

    df = df[(df["Average Trip Minutes"] < 100) & (df["totalTimeMin"] < 100)]
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
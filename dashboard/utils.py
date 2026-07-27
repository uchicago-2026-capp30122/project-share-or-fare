# This file defines variables that in previous versions were defined in app.py. This change was made to circumvent issues with circular imports.
import pandas as pd
from .visualization.transform import log_transform_time

df = pd.read_csv("./data/rideshare_transit_data.csv")
df["Pickup Neighborhood"] = df["Pickup Neighborhood"].astype("category")
df["Dropoff Neighborhood"] = df["Dropoff Neighborhood"].astype("category")
df["modes"] = df["modes"].astype("category")
df = df.drop(columns=[
    "Pickup Census Tract",
    "Dropoff Census Tract",
    # add any other unused columns here
])
float_cols = df.select_dtypes(include="float64").columns
df[float_cols] = df[float_cols].astype("float32")
df = log_transform_time(df)


dropdown_options = {
    "rideshareTime": "Rideshare Trip Time (Minutes)",
    "totalTransitTime": "Corresponding Transit Trip Time (Minutes)",
    "Log Rideshare Min": "Log of Rideshare Trip Time (Minutes)",
    "Log Transit Min": "Log of Transit Trip Time (Minutes)",
    "Float Trip Miles": "Rideshare Trip Distance (Miles)",
}
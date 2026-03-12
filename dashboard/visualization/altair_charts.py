import altair as alt
import pandas as pd

from .transform import dataset_sample, weighted_median


############################# Trip Level Analysis #############################
def distribution_of_rides(df: pd.DataFrame, row_chosen: str, dropdown_options: dict):
    """
    Creates a histogram of the distribution of ride times

    Arguments:
        df: a pandas dataframe with rideshare and transit data
        row_chosen: The dimension along which to create the histogram
        dropdown_options: A dictionary matching the row options to their
            lable names

    Returns: An altair chart

    Author: Sabrina
    """
    short_df = dataset_sample(df, 10)
    total_rides = short_df["Count"].sum()
    short_df["Percentage"] = (short_df["Count"] / total_rides) * 100

    step_size = {
        "rideshareTime": 5,
        "totalTransitTime": 5,
        "Log Rideshare Min": 0.1,
        "Log Transit Min": 0.1,
        "Float Trip Miles": 1,
    }

    domain_range = {
        "rideshareTime": [0, 100],
        "totalTransitTime": [0, 100],
        "Log Rideshare Min": [0, 2],
        "Log Transit Min": [0.4, 2.3],
        "Float Trip Miles": [0, 26],
    }

    chart = (
        alt.Chart(short_df)
        .mark_bar()
        .encode(
            alt.X(
                f"{row_chosen}:Q",
                title=dropdown_options[row_chosen],
                bin=alt.Bin(step=step_size[row_chosen]),
            ).scale(domain=domain_range[row_chosen]),
            alt.Y("sum(Percentage):Q", title="Percentage of Rides"),
        )
        .configure_axis(grid=False)
    )

    return chart


def transit_rideshare_comparison(df: pd.DataFrame):
    """
    Creates a scatter plot between rideshare time and transit time

    Arguments:
        df: The pandas dataframe with rideshare and transit data

    Returns: An altair chart, a scatter plot of rideshare and transit time

    Author: Sabrina
    """
    short_df = dataset_sample(df, 100)

    ratio_1_line = pd.DataFrame(
        {"rideshareTime": [0, 100], "totalTransitTime": [0, 100]}
    )

    chart = (
        alt.Chart(short_df)
        .mark_circle()
        .encode(
            alt.X("rideshareTime:Q")
            .title("Trip Time via Rideshare (Minutes)")
            .scale(domain=[0, 100]),
            alt.Y("totalTransitTime:Q")
            .title("Trip Time via Public Transportation (Minutes)")
            .scale(domain=[0, 100]),
        )
        + alt.Chart(ratio_1_line)
        .mark_line(color="lightgray", thickness=0.2)
        .encode(x="rideshareTime", y="totalTransitTime")
    ).configure_axis(grid=False)

    return chart


def distribution_of_ratio(df: pd.DataFrame):
    """
    Creates a hisogram of the transit to rideshare time ratio

    Arguments:
        df: The pandas dataframe with rideshare and transit data

    Returns: An altair chart, histogram of distribution of transit penalty score
        with 1:1 and median marked

    Author: Sabrina
    """
    # Create score bins by rounding to 1 decimal place
    df["transitPenalty"] = df["transitPenalty"].round(1)

    median = weighted_median(df, "transitPenalty")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X(
                "transitPenalty:O",
                title="Transit Penalty Score (Transit Time / Rideshare Time)",
                scale=alt.Scale(domain=[k / 10 for k in range(4, 51)]),
            ),
            alt.Y("sum(Count):Q", title="Number of Rides"),
        )
        .interactive()
        + alt.Chart(pd.DataFrame({"transitPenalty": [1]}))
        .mark_rule(color="lightgrey")
        .encode(
            alt.X(
                "transitPenalty:O",
                title="Transit Penalty Score (Transit Time / Rideshare Time)",
            )
        )
        + alt.Chart(pd.DataFrame({"transitPenalty": [median]}))
        .mark_rule(color="red")
        .encode(
            alt.X(
                "transitPenalty:O",
                title="Transit Penalty Score (Transit Time / Rideshare Time)",
            )
        )
    ).configure_axis(grid=False)

    return chart


def rides_by_month(df: pd.DataFrame):
    """
    Creates a bar chart of average daily rides per month

    Arguments:
        df: The pandas dataframe with rideshare and transit data

    Returns: An altair chart, bar chart of rides per day per month

    Author: Sabrina
    """
    # Agregate by month, summing rides
    rides_per_month = df.groupby("month", as_index=False).aggregate({"Count": "sum"})

    # Create a short dataframe of days in a month
    days_in_month = {
        "month": [k for k in range(1, 13)],
        "Days": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
    }
    days_df = pd.DataFrame(days_in_month)

    # Join agregated data with days in month to get average rides per day
    month_count_days = pd.merge(rides_per_month, days_df, on="month", how="left")
    month_count_days["Average Rides Per Day"] = (
        month_count_days["Count"] / month_count_days["Days"]
    )

    # Visualize
    chart = (
        alt.Chart(month_count_days)
        .mark_bar()
        .encode(
            alt.X("month:O", title="Month", axis=alt.Axis(labelAngle=0)),
            alt.Y("Average Rides Per Day:Q"),
        )
        .configure_axis(grid=False)
    )

    return chart


########################### Neighborhood Analysis ############################
def distance_vs_demand_quadrants(df):
    """
    Distance (miles) vs Rideshare Demand by Neighborhood
    Scatter Plot with Quadrants

    Authors: Waleed, Sarah
    """

    neighborhood_stats = df.sort_values(by="distance_wavg", ascending=False)

    # Averages for Quadrants (median)
    median_distance = neighborhood_stats["distance_wavg"].median()
    median_trips = neighborhood_stats["Count"].median()

    # Defining Quadrants
    def get_quadrant(row):
        if row["distance_wavg"] >= median_distance and row["Count"] >= median_trips:
            return "Long Distance / High Demand"
        elif row["distance_wavg"] < median_distance and row["Count"] >= median_trips:
            return "Short Distance / High Demand"
        elif row["distance_wavg"] >= median_distance and row["Count"] < median_trips:
            return "Long Distance / Low Demand"
        else:
            return "Short Distance / Low Demand"

    neighborhood_stats["Quadrant"] = neighborhood_stats.apply(get_quadrant, axis=1)

    # Scatter Plot
    points = (
        alt.Chart(neighborhood_stats)
        .mark_circle(size=180, opacity=0.6)
        .encode(
            x=alt.X("distance_wavg:Q", title="Average Trip Distance (Miles)"),
            y=alt.Y(
                "Count:Q",
                title="Log Total Rideshare Trips",
                scale=alt.Scale(type="log", domain=[1, 2000000]),
            ),
            tooltip=[
                "Pickup Neighborhood",
                alt.Tooltip(
                    "distance_wavg", format=".2f", title="Avg. Distance (Miles)"
                ),
                alt.Tooltip("Count", title="# Rides"),
            ],
        )
    )

    # Vertical (distance) and Horizontal (demand) Lines
    vline = (
        alt.Chart(pd.DataFrame({"x": [median_distance]}))
        .mark_rule(color="red")
        .encode(x="x:Q")
    )
    hline = (
        alt.Chart(pd.DataFrame({"y": [median_trips]}))
        .mark_rule(color="red")
        .encode(y="y:Q")
    )

    # Quadrant Labels
    quadrant_text = pd.DataFrame(
        {
            "x": [2.5, 12, 2.5, 12],
            "y": [5000000, 5000000, 1.5, 1.5],
            "label": [
                "Short Distance / High Demand",
                "Long Distance / High Demand",
                "Short Distance / Low Demand",
                "Long Distance / Low Demand",
            ],
        }
    )

    quadrant_labels = (
        alt.Chart(quadrant_text)
        .mark_text(fontSize=10, fontWeight="bold")
        .encode(x="x:Q", y="y:Q", text="label:N")
    )

    chart = (
        (points + vline + hline + quadrant_labels)
        .properties(width=700, height=500)
        .configure_axis(grid=False)
    )

    return chart


def transit_penalty_heatmap(pickup_neighborhods, neighborhood_route_data):
    """
    Author: Sarah
    """

    top_pickup_neighborhoods = (
        pickup_neighborhods.sort_values("Count", ascending=False)
        .head(20)["Pickup Neighborhood"]
        .values
    )
    top_pickup_neighborhoods = top_pickup_neighborhoods[
        (top_pickup_neighborhoods != "O'Hare")
        & (top_pickup_neighborhoods != "Garfield Ridge")
    ]

    heatmap_data = neighborhood_route_data[
        neighborhood_route_data["Pickup Neighborhood"].isin(top_pickup_neighborhoods)
        & neighborhood_route_data["Dropoff Neighborhood"].isin(top_pickup_neighborhoods)
    ]

    chart = (
        alt.Chart(heatmap_data)
        .mark_rect()
        .encode(
            x="Pickup Neighborhood",
            y="Dropoff Neighborhood",
            color=alt.Color("transitPenalty_wavg", title="Avg. Transit Penalty").scale(
                scheme="redyellowgreen", reverse=True
            ),
        )
    )

    return chart


def rideshare_count_heatmap(pickup_neighborhoods, neighborhood_route_data):
    """
    Author: Sarah
    """

    top_pickup_neighborhoods = (
        pickup_neighborhoods.sort_values("Count", ascending=False)
        .head(20)["Pickup Neighborhood"]
        .values
    )

    heatmap_data = neighborhood_route_data[
        neighborhood_route_data["Pickup Neighborhood"].isin(top_pickup_neighborhoods)
        & neighborhood_route_data["Dropoff Neighborhood"].isin(top_pickup_neighborhoods)
    ]

    chart = (
        alt.Chart(heatmap_data)
        .mark_rect()
        .encode(
            x="Pickup Neighborhood",
            y="Dropoff Neighborhood",
            color=alt.Color("Count", title="# Rides"),
        )
    )
    return chart


def corridor_price(df, is_high: bool):
    """
    Authors: Waleed, Sarah
    """

    corridors = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

    # Create corridor label
    corridors["corridor"] = (
        corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"]
    )

    # Remove low trip corridors as they are outliers
    corridors = corridors[corridors["Count"] > 20]

    # Get top 20 highest or lowest fares
    if is_high:
        corridors = corridors.nlargest(20, "tripCost_wavg")
    else:
        corridors = corridors.nsmallest(20, "tripCost_wavg")

    # Bar chart
    price_chart = (
        alt.Chart(corridors)
        .mark_bar()
        .encode(
            x=alt.X("tripCost_wavg:Q", title="Average Fare ($)"),
            y=alt.Y("corridor:N", sort="-x", title="Neighborhood Corridor"),
            tooltip=[
                "Pickup Neighborhood",
                "Dropoff Neighborhood",
                "tripCost_wavg",
                "Count",
            ],
            color=alt.Color("Count"),
        )
    )

    return price_chart

import pandas as pd
import altair as alt
from .transform_data import dataset_sample, weighted_median




def weighted_avg(group, value_col, weight_col):
    """
    Helper function for prep_data_for_map
    """
    return (group[value_col] * group[weight_col]).sum() / group[weight_col].sum()


############ Neighborhood Analysis ###################################

def most_pickups(df):
    """
    Top Neighborhoods with the most rideshare trips 
    Total rides per neighborhood (in descending order sort highest to lowest
    
    """
    rides_by_neighborhood = df.sort_values(
        by="Count", ascending=False).head(20)

    chart = alt.Chart(rides_by_neighborhood).mark_bar().encode(
        x="Count:Q",
        y=alt.Y("Pickup Neighborhood:N", sort='-x', title="Neighborhood"),
        tooltip=["Pickup Neighborhood", "Count"]
    ).properties(
        title="Top 20 Neighborhoods with Most Pickups"
    )

    return chart


def distance_vs_demand_quadrants(df):
    """
    Distance (miles) vs Rideshare Demand by Neighborhood
    Scatter Plot with Quadrants
    """
    neighborhood_stats = df.groupby(["Pickup Neighborhood"]).apply(
        lambda g: pd.Series({
            "distance_wavg": weighted_avg(g, "distance_wavg", "Count"),
            'Count': g['Count'].sum()
            })
            ).sort_values(
                by="Count",
                ascending=False).reset_index()

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
    points = alt.Chart(neighborhood_stats).mark_circle(size=180, opacity=0.6).encode(
        x=alt.X("distance_wavg:Q", title="Average Trip Distance (Miles)"),
        y=alt.Y("Count:Q", title="Log Total Rideshare Trips", scale=alt.Scale(type="log", domain=[1, 2000000])),
        color=alt.Color("Quadrant:N", legend=None),
        tooltip=["Pickup Neighborhood", 
                alt.Tooltip("distance_wavg",format= ".2f", title = "Avg. Distance (Miles)"), 
                alt.Tooltip("Count", title="# Rides")]
    )


    # Neighborhood Labels
    labels = alt.Chart(neighborhood_stats).mark_text(align="left", dx=6, dy=-3, fontSize=7).encode(x="distance_wavg:Q", y="Count:Q", text="Pickup Neighborhood:N")


    # Vertical (distance) and Horizontal (demand) Lines
    vline = alt.Chart(pd.DataFrame({"x":[median_distance]})).mark_rule(color="red").encode(x="x:Q")
    hline = alt.Chart(pd.DataFrame({"y":[median_trips]})).mark_rule(color="red").encode(y="y:Q")


    # Quadrant Labels
    quadrant_text = pd.DataFrame({
        "x": [2.5, 12, 2.5, 12],
        "y": [5000000, 5000000, 1.5, 1.5],
        "label": [
            "Short Distance / High Demand",
            "Long Distance / High Demand",
            "Short Distance / Low Demand",
            "Long Distance / Low Demand"
        ]
    })

    quadrant_labels = alt.Chart(quadrant_text).mark_text(fontSize=10, fontWeight="bold").encode(x="x:Q", y="y:Q", text="label:N") 


    chart = (points + vline + hline + quadrant_labels).properties(title="Trip Distance vs. Rideshare Demand by Pickup Neighborhood", width=700, height=500).configure_axis(
        grid=False)
    
    return chart



def corridor_bar_chart(df):
    """
    Transit vs Rideshare Connectivity by Neighborhood Corridors
    Bar Chart of Most and Least Connected Neighborhood Pairs
    A ratio close to 1 means transit and rideshare take similar time (better connectivity)
    Higher ratios (>1) indicate lower transit connectivity, meaning transit takes longer than rideshare
    """
    # Remove corridors where pickup and dropoff are the same
    corridors = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

    # Create corridor label
    corridors["corridor"] = (corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"])

    top_corridors = corridors.sort_values("Count", ascending=False).head(20)

    chart = alt.Chart(top_corridors).mark_bar().encode(
        x=alt.X("transitPenalty_wavg:Q", title="Average Transit Penalty"),
        y=alt.Y("corridor:N", sort="x", title="Neighborhood Corridor"),
        tooltip=["Pickup Neighborhood","Dropoff Neighborhood",
                alt.Tooltip("transitPenalty_wavg",format= ".2f", title="Transit Penalty")]
    ).properties(title="Transit Penalty for Top 20 Most Frequented Corridors",)
    
    return chart


def transit_penalty_heatmap(df):

    top_pickup_neighborhoods = df.sort_values("Count", ascending=False).head(20)["Pickup Neighborhood"].values
    top_pickup_neighborhoods = top_pickup_neighborhoods[(top_pickup_neighborhoods != "O'Hare") & (top_pickup_neighborhoods != "Garfield Ridge")]

    heatmap_data = df[df["Pickup Neighborhood"].isin(top_pickup_neighborhoods) & 
                      df["Dropoff Neighborhood"].isin(top_pickup_neighborhoods)]

    # heatmap_data = heatmap_data[["Pickup Neighborhood", "Dropoff Neighborhood", "transitPenalty_wavg", "Count", "tripCost_wavg"]]
    chart = alt.Chart(heatmap_data).mark_rect().encode(
        x='Pickup Neighborhood',
        y='Dropoff Neighborhood',
        color=alt.Color('transitPenalty_wavg', title="Avg. Transit Penalty").scale(scheme="redyellowgreen", reverse=True)).properties(
            title = "Transit Penalty for Most Frequented Neighborhoods (excl. airports)"
        )

    return chart



def corridor_highest_price(df):

    # connectivity_stats = connectivity_stats[connectivity_stats["Pickup Neighborhood"] != connectivity_stats["Dropoff Neighborhood"]]
    corridors = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

    # Create corridor label
    corridors["corridor"] = (corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"])

    # Remove low trip corridors as they are outliers
    corridors = corridors[corridors["Count"] > 20]

    # Get top 20 highest and lowest fares
    highest = corridors.nlargest(20, "tripCost_wavg")
    lowest = corridors.nsmallest(20, "tripCost_wavg")

    plot_df = pd.concat([highest, lowest])

    # Bar chart
    price_chart = alt.Chart(highest).mark_bar().encode(
        x=alt.X("tripCost_wavg:Q", title="Average Fare ($)"),
        y=alt.Y("corridor:N", sort="-x", title="Neighborhood Corridor"),
        tooltip=["Pickup Neighborhood", "Dropoff Neighborhood", "tripCost_wavg", "Count"],
        color=alt.Color("Count"),
    ).properties(title="Top 20 Highest Priced Neighborhood Corridors")

    return price_chart

def corridor_lowest_price(df):

    # connectivity_stats = connectivity_stats[connectivity_stats["Pickup Neighborhood"] != connectivity_stats["Dropoff Neighborhood"]]
    corridors = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

    # Create corridor label
    corridors["corridor"] = (corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"])

    # Remove low trip corridors as they are outliers
    corridors = corridors[(corridors["Count"] > 20) & 
                          (corridors["tripCost_wavg"]>0)]

    # Get top 20 highest and lowest fares
    highest = corridors.nlargest(20, "tripCost_wavg")
    lowest = corridors.nsmallest(20, "tripCost_wavg")

    # Bar chart
    price_chart = alt.Chart(lowest).mark_bar().encode(
        x=alt.X("tripCost_wavg:Q", title="Average Fare ($)"),
        y=alt.Y("corridor:N", sort="-x", title="Neighborhood Corridor"),
        color=alt.Color("Count"),
        tooltip=["Pickup Neighborhood", "Dropoff Neighborhood", 
                 alt.Tooltip("tripCost_wavg", format=".2f", title="Average Fare ($)"), "Count"]
    ).properties(title="Top 20 Lowest Priced Neighborhood Corridors")

    return price_chart


### Analysis 5:
## Top Most and Least Connected Travel Corridors in terms of Number of Trips (Volume)
# Pickup and Dropoff Neighborhood Connectivity Heatmap

# df = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

# flows = df.groupby(["Pickup Neighborhood","Dropoff Neighborhood"], as_index=False)["Count"].sum()

# most_connected = flows.nlargest(100,"Count").sort_values("Count", ascending=False)
# least_connected = flows[flows["Count"] == 1].head(100)

# most_connected["Group"] = "Most Connected"
# least_connected["Group"] = "Least Connected"

# corridors = pd.concat([most_connected, least_connected], ignore_index=True)

# dropdown = alt.binding_select(options=["Most Connected","Least Connected"], name="Show: ")
# selection = alt.selection_point(fields=["Group"], bind=dropdown, value="Most Connected")


# chart5 = alt.Chart(corridors).mark_rect().encode(
#     x="Pickup Neighborhood:N",
#     y="Dropoff Neighborhood:N",
#     color=alt.Color("Group:N",
#         scale=alt.Scale(domain=["Most Connected","Least Connected"],
#                         range=["green","red"]),
#         title="Corridor Type"
#     ),
#     tooltip=["Pickup Neighborhood","Dropoff Neighborhood","Count"]
# ).transform_filter(selection).add_params(selection).properties(
#     title="Most vs Least Connected Neighborhood Corridors"
# )

# chart5


df = pd.read_csv("./data/rideshare_transit_data.csv")

def distribution_of_rides(
    df: pd.DataFrame, row_chosen: str, dropdown_options: dict
):
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
    short_df["Percentage"] = (short_df['Count'] / total_rides) * 100

    step_size={
        'rideshareTime': 5,
        'totalTransitTime': 5,
        "Log Rideshare Min": 0.1,
        "Log Transit Min": 0.1,
        "Float Trip Miles": 1
    }

    domain_range ={
        'rideshareTime': [0, 100],
        'totalTransitTime': [0, 100],
        "Log Rideshare Min": [0, 2],
        "Log Transit Min": [0.4, 2.3],
        "Float Trip Miles": [0, 26]
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
            alt.Y(
                "sum(Percentage):Q", 
                title="Percentage of Rides"
            ),
        ).configure_axis(
            grid=False
        ).configure_axisY(
            titleAngle=0,
            titleAlign="right",
            titleY=-12,
            titleX=0,
        )
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
        {'rideshareTime': [0, 100], 'totalTransitTime': [0, 100]}
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
                .scale(domain=[0, 100])
        ) +
        alt.Chart(ratio_1_line)
        .mark_line(color='lightgray', thickness=0.2)
        .encode(
            x='rideshareTime', y='totalTransitTime'
        )
    ).configure_axis(
        grid=False
    ).configure_axisY(
        titleAngle=0,
        titleAlign="right",
        titleY=-12,
        titleX=0,
    )
    
    return chart


def distribution_of_ratio(df:pd.DataFrame):
    """
    Creates a hisogram of the transit to rideshare time ratio
    
    Author: Sabrina
    """
    df["transitPenalty"] = df["transitPenalty"].round(1)

    median = weighted_median(df, "transitPenalty")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X(
                "transitPenalty:O", 
                title="Transit Penalty Score (Transit Time / Rideshare Time)",
                scale=alt.Scale(domain=[k / 10 for k in range(4, 51)])
            ),
            alt.Y("sum(Count):Q", title="Number of Rides"),
        )
        .interactive() 
        + 
        alt.Chart(pd.DataFrame({'transitPenalty': [1]}))
        .mark_rule(color='lightgrey')
        .encode(
            alt.X(
                'transitPenalty:O',
                title="Transit Penalty Score (Transit Time / Rideshare Time)"
            )
        ) + 
        alt.Chart(pd.DataFrame({'transitPenalty': [median]}))
        .mark_rule(color='red')
        .encode(
            alt.X(
                'transitPenalty:O',
                title="Transit Penalty Score (Transit Time / Rideshare Time)"
            )
        )
    ).configure_axis(
        grid=False
    ).configure_axisY(
        titleAngle=0,
        titleAlign="right",
        titleY=-12,
        titleX=0,
    )

    return chart


def rides_by_month(df: pd.DataFrame):
    """
    Creates a bar chart of average daily rides per month

    Author: Sabrina
    """
    # Agregate by month, summing rides
    rides_per_month = (
        df.groupby('month', as_index=False)
        .aggregate({'Count': 'sum'})
        )

    # Create a short dataframe of days in a month
    days_in_month = {
        "month": [k for k in range(1, 13)],
        "Days": [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    }
    days_df = pd.DataFrame(days_in_month)

    # Join agregated data with days in month to get average rides per day
    month_count_days = pd.merge(
        rides_per_month, days_df, on='month', how='left'
    )
    month_count_days["Average Rides Per Day"] = (
        month_count_days["Count"] / month_count_days["Days"]
    )
    
    # Visualize
    chart = (
        alt.Chart(month_count_days)
        .mark_bar()
        .encode(
            alt.X(
                "month:O", 
                title="Month",
                axis=alt.Axis(labelAngle=0)
            ),
            alt.Y(
                "Average Rides Per Day:Q"
            ),
        ).configure_axis(
            grid=False
        ).configure_axisY(
            titleAngle=0,
            titleAlign="right",
            titleY=-12,
            titleX=0,
        )
    )
    
    return chart


def ratio_by_month(df: pd.DataFrame):
    """
    Creates a line graph showing the change in transit-rideshare time ratio
    over months.  Compares that to temperature.

    Author: Sabrina
    """
    # Agregate by month, averaging transit-rideshare ratio
    ratio_per_month = (
        df.groupby('month', as_index=False)
        .aggregate({'transitPenalty': 'mean'})
        )
    
    # Create a small dataframe of average monthly temperature in 2025
    # Average monthly temperature for Chicago in 2025 found at
    # https://www.weather.gov/wrh/Climate?wfo=lot
    avg_temp_2025 = {
        "month": [k for k in range(1, 13)],
        "Temp": [
            22.6,
            27.2,
            44.4,
            50.8,
            58.0,
            74.2,
            77.5,
            73.3,
            69.3,
            58.1,
            42.4,
            27.0
        ]
    }
    temperature_df = pd.DataFrame(avg_temp_2025)

    # Line graph of transit-rideshare-ratio
    ratio_line = (
        alt.Chart(ratio_per_month)
        .mark_line(point=True)
        .encode(
            alt.X(
                "month:O", 
                title="Month",
                axis=alt.Axis(labelAngle=0)
            ),
            alt.Y(
                "transitPenalty:Q",
                title="Average Transit Time to Rideshare Time Ratio",
                axis=alt.Axis(orient='left')
            ).scale(domain=[2, 2.7]),
        )
    )

    # Line graph of temperature, with y axis decreasing to make comparison
    # with ratio easier
    temperature_line = (
        alt.Chart(temperature_df)
        .mark_line(color='lightgray', thickness=0.2)
        .encode(
            alt.X(
                'month:O',
                title="Month",
                axis=alt.Axis(labelAngle=0)
            ),
            alt.Y(
                'Temp:Q',
                title="Average Temperature (F) -- Decreasing",
                axis=alt.Axis(orient='right'),
                scale=alt.Scale(reverse=True)
            ).scale(domain=[100, 0]),
        )
    )

    chart = (
        ratio_line + temperature_line
    ).resolve_scale(
        y='independent'
    ).configure_axisY(
        titleAngle=0,
        titleAlign="right",
        titleY=-12,
        titleX=0
    ).configure_axisRight(
        titleAngle=0,
        titleAlign="left",
        titleY=-12,
        titleX=0
    )

    return chart
import pandas as pd
import altair as alt
from .transform_data import dataset_sample

df = pd.read_csv("./data/small_medium_merged_neighborhood.csv")

### Analysis 1:
## Top Neighborhoods with the most rideshare trips
# Total rides per neighborhood (in descending order)

rides_by_neighborhood = (
    df.groupby("Pickup Neighborhood")["Count"]
    .sum()
    .reset_index()
)

# sort highest to lowest
rides_by_neighborhood = rides_by_neighborhood.sort_values(
    by="Count", ascending=False).head(20)

chart1 = alt.Chart(rides_by_neighborhood).mark_bar().encode(
    x="Count:Q",
    y=alt.Y("Pickup Neighborhood:N", sort='-x', title="Neighborhood"),
    tooltip=["Pickup Neighborhood", "Count"]
).properties(
    title="Top 20 Neighborhoods with Most Rideshare Trips"
)

chart1
chart1.show()



### Analysis 2:
## Distance (miles) vs Rideshare Demand by Neighborhood
# Scatter Plot with Quadrants

neighborhood_stats = (
    df.groupby("Pickup Neighborhood")
    .agg({
        "Float Trip Miles": "mean",   # average distance of rides
        "Count": "sum"                # total rideshare demand or trips
    })
    .reset_index())


# Only neighborhoods with the longest rides
neighborhood_stats = neighborhood_stats.sort_values(
    by="Float Trip Miles",
    ascending=False).head(20)


# Averages for Quadrants (median)
median_distance = neighborhood_stats["Float Trip Miles"].median()
median_trips = neighborhood_stats["Count"].median()


# Defining Quadrans
def get_quadrant(row):
    if row["Float Trip Miles"] >= median_distance and row["Count"] >= median_trips:
        return "Long Distance / High Demand"
    elif row["Float Trip Miles"] < median_distance and row["Count"] >= median_trips:
        return "Short Distance / High Demand"
    elif row["Float Trip Miles"] >= median_distance and row["Count"] < median_trips:
        return "Long Distance / Low Demand"
    else:
        return "Short Distance / Low Demand"

neighborhood_stats["Quadrant"] = neighborhood_stats.apply(get_quadrant, axis=1)


# Scatter Plot
points = alt.Chart(neighborhood_stats).mark_circle(size=180, opacity=0.6).encode(
    x=alt.X("Float Trip Miles:Q", title="Average Trip Distance (Miles)"),
    y=alt.Y("Count:Q", title="Total Rideshare Trips", scale=alt.Scale(type="log", domain=[1, 2000000])),
    color=alt.Color("Quadrant:N", legend=None),
    tooltip=["Pickup Neighborhood", "Float Trip Miles", "Count"]
)


# Neighborhood Labels
labels = alt.Chart(neighborhood_stats).mark_text(align="left", dx=6, dy=-3, fontSize=7).encode(x="Float Trip Miles:Q", y="Count:Q", text="Pickup Neighborhood:N")


# Vertical (distance) and Horizontal (demand) Lines
vline = alt.Chart(pd.DataFrame({"x":[median_distance]})).mark_rule(color="red").encode(x="x:Q")
hline = alt.Chart(pd.DataFrame({"y":[median_trips]})).mark_rule(color="red").encode(y="y:Q")


# Quadrant Labels
quadrant_text = pd.DataFrame({
    "x": [4, 13, 4, 13],
    "y": [5000000, 5000000, 1.5, 1.5],
    "label": [
        "Short Distance / High Demand",
        "Long Distance / High Demand",
        "Short Distance / Low Demand",
        "Long Distance / Low Demand"
    ]
})

quadrant_labels = alt.Chart(quadrant_text).mark_text(fontSize=10, fontWeight="bold").encode(x="x:Q", y="y:Q", text="label:N")


chart2 = (points + labels + vline + hline + quadrant_labels).properties(title="Distance vs Rideshare Demand by Neighborhood", width=700, height=500)

chart2
chart2.show()




### Analysis 3:
## Transit vs Rideshare Connectivity by Neighborhood Corridors
# Bar Chart of Most and Least Connected Neighborhood Pairs

# Connectivity Ratio: Transit Time / Rideshare Time
# A ratio close to 1 means transit and rideshare take similar time (better connectivity)
# Higher ratios (>1) indicate lower transit connectivity, meaning transit takes longer than rideshare
# Convert from string to numeric value
df["totalTime"] = df["totalTime"].str.replace("s","").astype(float)
df["Average Trip Seconds"] = pd.to_numeric(df["Average Trip Seconds"], errors="coerce")

df["Connectivity Ratio"] = df["totalTime"] / df["Average Trip Seconds"]


connectivity_stats = (
    df.groupby(["Pickup Neighborhood","Dropoff Neighborhood"])
    .agg({"Connectivity Ratio": "mean"})
    .reset_index())


# Remove corridors where pickup and dropoff are the same
connectivity_stats = connectivity_stats[connectivity_stats["Pickup Neighborhood"] != connectivity_stats["Dropoff Neighborhood"]]

# Create corridor label
connectivity_stats["corridor"] = (connectivity_stats["Pickup Neighborhood"] + " → " + connectivity_stats["Dropoff Neighborhood"])

# Most connected (transit closest to rideshare)
most_connected = connectivity_stats.nsmallest(20, "Connectivity Ratio")

# Least connected (transit much slower)
least_connected = connectivity_stats.nlargest(20, "Connectivity Ratio")

plot_df = pd.concat([most_connected, least_connected])

chart3 = alt.Chart(plot_df).mark_bar().encode(
    x=alt.X("Connectivity Ratio:Q", title="Transit Time / Rideshare Time"),
    y=alt.Y("corridor:N", sort="x", title="Neighborhood Corridor"),
    tooltip=["Pickup Neighborhood","Dropoff Neighborhood","Connectivity Ratio"]
).properties(title="Most and Least Transit-Connected Neighborhoods",)

chart3
chart3.show()




### Analysis 4:
## Highest and Lowest Priced Neighborhood Corridors

# Remove same pickup and dropoff
df = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

# Aggregate corridors
corridors = (
    df.groupby(["Pickup Neighborhood", "Dropoff Neighborhood"])
      .agg({
          "Average Fare": "mean",
          "Count": "sum"
      })
      .reset_index()
)

# Remove low trip corridors as they are outliers
corridors = corridors[corridors["Count"] > 20]

# Create corridor labels
corridors["corridor"] = (corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"])

# Get top 20 highest and lowest fares
highest = corridors.nlargest(20, "Average Fare")
lowest = corridors.nsmallest(20, "Average Fare")

plot_df = pd.concat([highest, lowest])

# Bar chart
price_chart = alt.Chart(plot_df).mark_bar().encode(
    x=alt.X("Average Fare:Q", title="Average Fare ($)"),
    y=alt.Y("corridor:N", sort="-x", title="Neighborhood Corridor"),
    color=alt.condition(
        alt.datum["Average Fare"] > plot_df["Average Fare"].median(),
        alt.value("green"),
        alt.value("red")
    ),
    tooltip=["Pickup Neighborhood", "Dropoff Neighborhood", "Average Fare", "Count"]
).properties(title="Top 20 Highest and Lowest Priced Neighborhood Corridors")

price_chart
price_chart.show()




### Analysis 5:
## Top Most and Least Connected Travel Corridors in terms of Number of Trips (Volume)
# Pickup and Dropoff Neighborhood Connectivity Heatmap

df = df[df["Pickup Neighborhood"] != df["Dropoff Neighborhood"]]

flows = df.groupby(["Pickup Neighborhood","Dropoff Neighborhood"], as_index=False)["Count"].sum()

most_connected = flows.nlargest(100,"Count").sort_values("Count", ascending=False)
least_connected = flows[flows["Count"] == 1].head(100)

most_connected["Group"] = "Most Connected"
least_connected["Group"] = "Least Connected"

corridors = pd.concat([most_connected, least_connected], ignore_index=True)

dropdown = alt.binding_select(options=["Most Connected","Least Connected"], name="Show: ")
selection = alt.selection_point(fields=["Group"], bind=dropdown, value="Most Connected")


chart5 = alt.Chart(corridors).mark_rect().encode(
    x="Pickup Neighborhood:N",
    y="Dropoff Neighborhood:N",
    color=alt.Color("Group:N",
        scale=alt.Scale(domain=["Most Connected","Least Connected"],
                        range=["green","red"]),
        title="Corridor Type"
    ),
    tooltip=["Pickup Neighborhood","Dropoff Neighborhood","Count"]
).transform_filter(selection).add_params(selection).properties(
    title="Most vs Least Connected Neighborhood Corridors"
)

chart5


def distribution_of_rides(df: pd.DataFrame, row_chosen: str, dropdown_options):
    """
    Creates a histogram of the distribution of ride times

    Author: Sabrina
    """
    short_df = dataset_sample(df, 10)

    chart = (
        alt.Chart(short_df)
        .mark_bar()
        .encode(
            alt.X(
                f"{row_chosen}:Q",
                title=dropdown_options[row_chosen],
                bin=alt.Bin(step=5)
            ),
            alt.Y("sum(Count):Q", title="Number of Rides"),
        )
    )
    
    return chart


def transit_rideshare_comparison(df: pd.DataFrame):
    """
    Creates a scatter plot between rideshare time and transit time

    Author: Sabrina
    """
    short_df = dataset_sample(df, 100)

    ratio_1_line = pd.DataFrame(
        {'rideshareTime': [0, 100], 'totalTransitTime': [0, 100]}
    )

    chart = (
        alt.Chart(short_df)
        .mark_circle()#size=60)
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
    )
    
    return chart


def distribution_of_ratio(df:pd.DataFrame):
    """
    Creates a hisogram of the transit to rideshare time ratio
    
    Author: Sabrina
    """
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X(
                "transitPenalty:O", 
                title="Ratio of Transit to Rideshare Time"),
            alt.Y("sum(Count):Q", title="Number of Rides"),
        )
        .interactive() 
        + 
        alt.Chart(pd.DataFrame({'transitPenalty': [1]}))
        .mark_rule(color='red')
        .encode(
            alt.X(
                'transitPenalty:O',
                title="Ratio of Transit to Rideshare Time"
            )
        )
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
        )
        .configure_axisY(
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
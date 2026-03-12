import altair as alt
import pandas as pd


def ratio_by_month(df: pd.DataFrame):
    """
    Creates a line graph showing the change in transit-rideshare time ratio
    over months.  Compares that to temperature.

    Author: Sabrina
    """
    # Agregate by month, averaging transit-rideshare ratio
    ratio_per_month = df.groupby("month", as_index=False).aggregate(
        {"transitPenalty": "mean"}
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
            27.0,
        ],
    }
    temperature_df = pd.DataFrame(avg_temp_2025)

    # Line graph of transit-rideshare-ratio
    ratio_line = (
        alt.Chart(ratio_per_month)
        .mark_line(point=True)
        .encode(
            alt.X("month:O", title="Month", axis=alt.Axis(labelAngle=0)),
            alt.Y(
                "transitPenalty:Q",
                title="Average Transit Time to Rideshare Time Ratio",
                axis=alt.Axis(orient="left"),
            ).scale(domain=[2, 2.7]),
        )
    )

    # Line graph of temperature, with y axis decreasing to make comparison
    # with ratio easier
    temperature_line = (
        alt.Chart(temperature_df)
        .mark_line(color="lightgray", thickness=0.2)
        .encode(
            alt.X("month:O", title="Month", axis=alt.Axis(labelAngle=0)),
            alt.Y(
                "Temp:Q",
                title="Average Temperature (F) -- Decreasing",
                axis=alt.Axis(orient="right"),
                scale=alt.Scale(reverse=True),
            ).scale(domain=[100, 0]),
        )
    )

    chart = (
        (ratio_line + temperature_line)
        .resolve_scale(y="independent")
        .configure_axisY(titleAngle=0, titleAlign="right", titleY=-12, titleX=0)
        .configure_axisRight(titleAngle=0, titleAlign="left", titleY=-12, titleX=0)
    )

    return chart


def most_pickups(df):
    """
    Top Neighborhoods with the most rideshare trips
    Total rides per neighborhood (in descending order sort highest to lowest

    """
    rides_by_neighborhood = df.sort_values(by="Count", ascending=False).head(20)

    chart = (
        alt.Chart(rides_by_neighborhood)
        .mark_bar()
        .encode(
            x="Count:Q",
            y=alt.Y("Pickup Neighborhood:N", sort="-x", title="Neighborhood"),
            tooltip=["Pickup Neighborhood", "Count"],
        )
        .properties(title="Top 20 Neighborhoods with Most Pickups")
    )

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
    corridors["corridor"] = (
        corridors["Pickup Neighborhood"] + " → " + corridors["Dropoff Neighborhood"]
    )

    top_corridors = corridors.sort_values("Count", ascending=False).head(20)

    chart = (
        alt.Chart(top_corridors)
        .mark_bar()
        .encode(
            x=alt.X("transitPenalty_wavg:Q", title="Average Transit Penalty"),
            y=alt.Y("corridor:N", sort="x", title="Neighborhood Corridor"),
            tooltip=[
                "Pickup Neighborhood",
                "Dropoff Neighborhood",
                alt.Tooltip(
                    "transitPenalty_wavg", format=".2f", title="Transit Penalty"
                ),
            ],
        )
        .properties(
            title="Transit Penalty for Top 20 Most Frequented Corridors",
        )
    )

    return chart

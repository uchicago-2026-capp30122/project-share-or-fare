import pandas as pd


def clean_route_data(route_data):
    """
    Cleans and renames time fields on disaggregated data
    """
    # drop NAs
    route_data = route_data.dropna()

    # convert totalTime field to int and minutes
    route_data["totalTime"] = (
        route_data["totalTime"].apply(lambda s: int(str(s)[:-1])) / 60
    )

    # convert ride share time to minutes
    route_data["Average Trip Minutes"] = route_data["Average Trip Seconds"] / 60

    # Rename columns for clarity
    route_data = route_data.rename(
        columns={
            "totalTime": "totalTransitTime",
            "Average Trip Minutes": "rideshareTime",
        }
    )

    # Add transitPenalty and color mapping
    route_data["transitPenalty"] = (
        route_data["totalTransitTime"] / route_data["rideshareTime"]
    )

    return route_data


def join_neighborhood_polygons(data, neighborhood_boundaries):
    """
    Merge in polygon data, helper function for prep_data_for_map
    """

    # Pickup neighborhood
    data = data.merge(
        neighborhood_boundaries[["the_geom", "PRI_NEIGH"]],
        left_on="Pickup Neighborhood",
        right_on="PRI_NEIGH",
        how="left",
    )
    data = data.rename(columns={"the_geom": "Pickup Neighborhood Polygon"})

    # Dropoff neighborhood
    data = data.merge(
        neighborhood_boundaries[["the_geom", "PRI_NEIGH"]],
        left_on="Dropoff Neighborhood",
        right_on="PRI_NEIGH",
        how="left",
    )
    data = data.rename(columns={"the_geom": "Dropoff Neighborhood Polygon"})

    # Filter out missing values
    data = data[
        (data["Dropoff Neighborhood Polygon"] != "")
        & (data["Pickup Neighborhood Polygon"] != "")
    ]

    return data


def weighted_avg(group, value_col, weight_col):
    """
    Helper function for prep_data_for_map
    """
    return (group[value_col] * group[weight_col]).sum() / group[weight_col].sum()


def prep_data_for_map(route_data, neighborhood_boundaries):
    """
    This aggregates by neighborhood, merges in the polygon data,
    and adds the color mapping variable based on transit Penalty
    """
    # First aggregate by pickup and dropoff neighborhood and take weighted avgs
    neighborhood_level_data = (
        route_data.groupby(["Pickup Neighborhood", "Dropoff Neighborhood"])
        .apply(
            lambda g: pd.Series(
                {
                    "totalTransitTime_wavg": weighted_avg(
                        g, "totalTransitTime", "Count"
                    ),
                    "rideshareTime_wavg": weighted_avg(g, "rideshareTime", "Count"),
                    "tripCost_wavg": weighted_avg(g, "Average Trip Total", "Count"),
                    "transitPenalty_wavg": weighted_avg(g, "transitPenalty", "Count"),
                    "distance_wavg": weighted_avg(g, "Float Trip Miles", "Count"),
                    "Count": g["Count"].sum(),
                }
            )
        )
        .reset_index()
    )

    # Add color mapping based on transitPenalty
    bins = [0, 0.25, 0.50, 0.75, 1]
    labels = ["green", "yellow", "orange", "red"]
    neighborhood_level_data["transitPenaltyColor"] = pd.cut(
        neighborhood_level_data["transitPenalty_wavg"].rank(pct=True),
        bins=bins,
        labels=labels,
    )

    neighborhood_level_data_w_polygons = join_neighborhood_polygons(
        neighborhood_level_data, neighborhood_boundaries
    )

    return neighborhood_level_data_w_polygons

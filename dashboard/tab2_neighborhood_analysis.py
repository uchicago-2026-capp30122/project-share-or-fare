import pandas as pd
import html
from dash import html
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from .visualization.transform import weighted_avg, get_text
from .visualization.altair_charts import (
    distance_vs_demand_quadrants,
    transit_penalty_heatmap,
    rideshare_count_heatmap,
    corridor_price,
)

# Load captions
frequency_heatmap_text = get_text("dashboard/text/frequency_heatmap.txt")
transit_penalty_heatmap_text = get_text("dashboard/text/transit_penalty_heatmap.txt")
distance_vs_demand_quadrants_text = get_text(
    "dashboard/text/distance_vs_demand_quadrants.txt"
)
corridor_highest_price_text = get_text("dashboard/text/corridor_highest_price.txt")
corridor_lowest_price_text = get_text("dashboard/text/corridor_lowest_price.txt")

neighborhood_route_data = pd.read_csv("data/neighborhood_route_data.csv")

pickup_neighborhoods = (
    neighborhood_route_data.groupby(["Pickup Neighborhood"])
    .apply(
        lambda g: pd.Series(
            {
                "totalTransitTime_wavg": weighted_avg(
                    g, "totalTransitTime_wavg", "Count"
                ),
                "rideshareTime_wavg": weighted_avg(g, "rideshareTime_wavg", "Count"),
                "tripCost_wavg": weighted_avg(g, "tripCost_wavg", "Count"),
                "transitPenalty_wavg": weighted_avg(g, "transitPenalty_wavg", "Count"),
                "distance_wavg": weighted_avg(g, "distance_wavg", "Count"),
                "Count": g["Count"].sum(),
            }
        )
    )
    .reset_index()
)


distance_vs_demand_quadrants_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=distance_vs_demand_quadrants(pickup_neighborhoods).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"},
)


transit_penalty_heatmap_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=transit_penalty_heatmap(
        pickup_neighborhoods, neighborhood_route_data
    ).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"},
)

rideshare_count_heatmap_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=rideshare_count_heatmap(
        pickup_neighborhoods, neighborhood_route_data
    ).to_dict(),
    style={"display": "flex", "justifyContent": "center"},
)

corridor_highest_price_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=corridor_price(neighborhood_route_data, is_high=True).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"},
)

corridor_lowest_price_analysis = dvc.Vega(
    opt={"renderer": "svg", "actions": False},
    spec=corridor_price(neighborhood_route_data, is_high=False).to_dict(),
    style={"display": "flex", "justifyContent": "center", "width": "100%"},
)


graph1 = dbc.Card(
    [
        dbc.CardHeader("Most Frequented Neighborhood Corridors"),
        dbc.CardBody(
            [
                html.Div([rideshare_count_heatmap_analysis]),
                html.P(frequency_heatmap_text, className="card-text"),
            ]
        ),
    ]
)


graph2 = dbc.Card(
    [
        dbc.CardHeader(
            "Transit Penalty for Most Frequented Neighborhood Corridors (excl. airports)"
        ),
        dbc.CardBody(
            [
                html.Div([transit_penalty_heatmap_analysis]),
                html.P(transit_penalty_heatmap_text, className="card-text"),
            ]
        ),
    ]
)


graph3 = dbc.Card(
    [
        dbc.CardHeader("Trip Distance vs. Demand"),
        dbc.CardBody([html.Div([distance_vs_demand_quadrants_analysis])]),
    ]
)

text3 = dbc.Card(
    [dbc.CardBody([html.P(distance_vs_demand_quadrants_text, className="card-text")])]
)

graph4 = dbc.Card(
    [
        dbc.CardHeader("Top 20 Highest Priced Neighborhood Corridors"),
        dbc.CardBody(
            [
                html.Div([corridor_highest_price_analysis]),
                html.P(corridor_highest_price_text, className="card-text"),
            ]
        ),
    ]
)

graph5 = dbc.Card(
    [
        dbc.CardHeader("Top 20 Lowest Priced Neighborhood Corridors"),
        dbc.CardBody(
            [
                html.Div([corridor_lowest_price_analysis]),
                html.P(corridor_lowest_price_text, className="card-text"),
            ]
        ),
    ]
)


row_1 = dbc.Row(
    [
        dbc.Col(graph1),
        dbc.Col(graph2),
    ],
    className="mb-4",
)

row_2 = dbc.Row(
    [
        dbc.Col(graph4),
        dbc.Col(graph5),
    ],
    className="mb-4",
)

row_3 = dbc.Row(
    [dbc.Col(graph3), dbc.Col(text3)],
    className="mb-4",
)

neighborhood_tab = html.Div([row_1, row_2, row_3])

import html

import dash_bootstrap_components as dbc
from dash import html

from .visualization.transform import get_text

discussion_text = get_text("dashboard/text/discussion.txt")

discussion = [
    dbc.Col(
        children=[
            html.Hr(),
            html.H3("Discussion of Results"),
            html.Hr(),
            html.Div(children=discussion_text, style={"white-space": "pre-wrap"}),
        ],
        width={"size": 10, "offset": 1},
    )
]

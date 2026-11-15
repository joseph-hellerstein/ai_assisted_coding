"""Layout of the Survey Taker tab."""
from dash import dcc, html

import src.constants as cn


def taker_layout() -> html.Div:
    return html.Div([
        html.H3("Take a survey"),
        dcc.Dropdown(id=cn.TAKER_SURVEY_SELECT, placeholder="Choose a survey..."),
        html.Div(id=cn.TAKER_FORM, style={"marginTop": "16px"}),
    ], style={"maxWidth": "700px", "margin": "0 auto"})

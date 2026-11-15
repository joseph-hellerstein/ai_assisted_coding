"""Layout of the Survey Analyzer tab."""
from dash import dcc, html

import src.constants as cn


def analyzer_layout() -> html.Div:
    return html.Div([
        html.H3("Analyze a survey"),
        dcc.Dropdown(id=cn.ANALYZER_SURVEY_SELECT, placeholder="Choose a survey..."),
        html.Div(id=cn.ANALYZER_RESULTS, style={"marginTop": "16px"}),
    ], style={"maxWidth": "900px", "margin": "0 auto"})

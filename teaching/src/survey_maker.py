"""Layout of the Survey Maker tab: a title, a description, and fixed question rows."""
from dash import dcc, html

import src.constants as cn

QUESTION_TYPES = ["text", "yesno", "checkbox"]


def _question_row(row: int) -> html.Div:
    return html.Div([
        html.Label(f"Question {row + 1}", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id={"type": cn.MAKER_Q_TYPE, "row": row},
            options=QUESTION_TYPES, value="text", clearable=False,
            style={"width": "160px"},
        ),
        dcc.Input(
            id={"type": cn.MAKER_Q_TEXT, "row": row}, type="text",
            placeholder="Question text (leave blank to skip)",
            style={"width": "100%", "marginTop": "4px"},
        ),
        dcc.Textarea(
            id={"type": cn.MAKER_Q_OPTIONS, "row": row},
            placeholder="Options, one per line (checkbox only)",
            style={"width": "100%", "height": "60px", "marginTop": "4px"},
        ),
    ], style={"marginBottom": "16px"})


def maker_layout() -> html.Div:
    return html.Div([
        html.H3("Make a survey"),
        dcc.Input(id=cn.MAKER_TITLE, type="text", placeholder="Survey title", style={"width": "100%"}),
        dcc.Textarea(id=cn.MAKER_DESCRIPTION, placeholder="Description (optional)",
                     style={"width": "100%", "marginTop": "8px"}),
        html.Div([_question_row(row) for row in range(cn.N_QUESTION_ROWS)], style={"marginTop": "16px"}),
        html.Button("Save Survey", id=cn.MAKER_SAVE),
        html.Div(id=cn.MAKER_STATUS, style={"marginTop": "12px"}),
    ], style={"maxWidth": "700px", "margin": "0 auto"})

"""The Survey Manager teaching edition: the Dash app, its layout, and its callbacks.

Run it from the teaching/ folder with:  python -m src.app
"""
from dash import ALL, Dash, Input, Output, State, callback, dcc, html

import src.constants as cn
from src.form_logic import assemble_questions_from_state
from src.models import Survey, generate_id
from src.storage import save_survey
from src.survey_analyzer import analyzer_layout
from src.survey_maker import maker_layout
from src.survey_taker import taker_layout

WARNING = {"color": "darkorange"}
SUCCESS = {"color": "green"}

app = Dash(__name__, suppress_callback_exceptions=True, title="Survey Manager (teaching)")

app.layout = html.Div([
    html.H1("Survey Manager", style={"textAlign": "center"}),
    dcc.Tabs(id=cn.MAIN_TABS, value="maker", children=[
        dcc.Tab(label="Survey Maker", value="maker", children=maker_layout()),
        dcc.Tab(label="Survey Taker", value="taker", children=taker_layout()),
        dcc.Tab(label="Survey Analyzer", value="analyzer", children=analyzer_layout()),
    ]),
])


# 1. Survey Maker: save the form as a new survey.
@callback(
    Output(cn.MAKER_STATUS, "children"),
    Input(cn.MAKER_SAVE, "n_clicks"),
    State(cn.MAKER_TITLE, "value"),
    State(cn.MAKER_DESCRIPTION, "value"),
    State({"type": cn.MAKER_Q_TYPE, "row": ALL}, "value"),
    State({"type": cn.MAKER_Q_TEXT, "row": ALL}, "value"),
    State({"type": cn.MAKER_Q_OPTIONS, "row": ALL}, "value"),
    prevent_initial_call=True,
)
def save_survey_callback(n_clicks, title, description, types, texts, options_texts):
    title = (title or "").strip()
    if not title:
        return html.Div("⚠️ Please enter a survey title.", style=WARNING)

    questions, errors = assemble_questions_from_state(types, texts, options_texts)
    if errors:
        return html.Div([html.Div(f"⚠️ {error}") for error in errors], style=WARNING)

    survey = Survey(id=generate_id("srv_"), title=title,
                    description=(description or "").strip(), questions=questions)
    save_survey(survey)
    return html.Div(f"✅ Survey '{title}' saved.", style=SUCCESS)


if __name__ == "__main__":
    app.run(debug=True, port=cn.PORT)

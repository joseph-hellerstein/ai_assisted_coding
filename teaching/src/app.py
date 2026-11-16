"""The Survey Manager teaching edition: the Dash app, its layout, and its callbacks.

Run it from the teaching/ folder with:  python -m src.app
"""
from datetime import datetime

from dash import ALL, Dash, Input, Output, State, callback, dcc, html, no_update

import src.constants as cn
from src.form_logic import assemble_questions_from_state, build_response_answers, is_valid_respondent_id  # type: ignore
from src.models import Response, Survey, generate_id  # type: ignore
from src.storage import list_surveys, load_responses, load_survey, save_response, save_survey  # type: ignore
from src.survey_analyzer import analyzer_layout, build_results  # type: ignore
from src.survey_maker import maker_layout  # type: ignore
from src.survey_taker import render_survey_form, taker_layout  # type: ignore

WARNING = {"color": "darkorange"}
SUCCESS = {"color": "green"}
SURVEY_GONE = "⚠️ This survey no longer exists."

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


# 2. Every tab switch: refresh the survey dropdowns on the Taker and Analyzer tabs.
@callback(
    Output(cn.TAKER_SURVEY_SELECT, "options"),
    Output(cn.ANALYZER_SURVEY_SELECT, "options"),
    Input(cn.MAIN_TABS, "value"),
)
def refresh_survey_lists(tab):
    options = [{"label": s["title"], "value": s["id"]} for s in list_surveys()]
    return options, options


# 3. Survey Taker: show the form for the chosen survey.
@callback(
    Output(cn.TAKER_FORM, "children"),
    Input(cn.TAKER_SURVEY_SELECT, "value"),
)
def show_survey(survey_id):
    if not survey_id:
        return []
    survey = load_survey(survey_id)
    if survey is None:
        return html.Div(SURVEY_GONE, style=WARNING)
    return render_survey_form(survey)


# 4. Survey Taker: check the respondent's ID and save their answers.
@callback(
    Output(cn.TAKER_STATUS, "children"),
    Output(cn.TAKER_SUBMIT, "disabled"),
    Input(cn.TAKER_SUBMIT, "n_clicks"),
    State(cn.TAKER_SURVEY_SELECT, "value"),
    State(cn.TAKER_RESPONDENT_ID, "value"),
    State({"type": cn.ANSWER, "qid": ALL}, "value"),
    State({"type": cn.ANSWER, "qid": ALL}, "id"),
    prevent_initial_call=True,
)
def submit_survey_response(n_clicks, survey_id, respondent_id, values, ids):
    if load_survey(survey_id) is None:
        return html.Div(SURVEY_GONE, style=WARNING), no_update
    if not is_valid_respondent_id(respondent_id):
        return html.Div("⚠️ Your ID must be exactly 5 digits.", style=WARNING), no_update

    response = Response(
        id=generate_id("resp_"),
        survey_id=survey_id,
        submitted_at=datetime.now().isoformat(timespec="seconds"),
        respondent_id=respondent_id,
        answers=build_response_answers([i["qid"] for i in ids], values),
    )
    save_response(response)
    return html.Div("✅ Thank you! Your response has been recorded.", style=SUCCESS), True


# 5. Survey Analyzer: show charts and a table for the chosen survey.
@callback(
    Output(cn.ANALYZER_RESULTS, "children"),
    Input(cn.ANALYZER_SURVEY_SELECT, "value"),
)
def analyze_survey(survey_id):
    if not survey_id:
        return []
    survey = load_survey(survey_id)
    if survey is None:
        return html.Div(SURVEY_GONE, style=WARNING)
    return build_results(survey, load_responses(survey_id))


if __name__ == "__main__":
    app.run(debug=True, port=cn.PORT)

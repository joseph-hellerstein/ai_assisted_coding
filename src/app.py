"""Main Dash application for Survey Manager."""

import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure src directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ALL, MATCH
import dash

import survey_maker  # type: ignore
import survey_taker  # type: ignore
import survey_analyzer  # type: ignore
import constants as cn  # type: ignore
from models import Survey, Response, generate_id  # type: ignore
from storage import save_survey, load_survey, list_surveys, save_response, load_responses, delete_survey  # type: ignore
from form_logic import (  # type: ignore
    type_visibility,
    section_style,
    extract_clicked_qid,
    assemble_questions_from_state,
    remove_question_by_qid,
    build_response_answers_from_state,
)


# ===== Create the app instance at module level so callbacks can register =====
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Survey Manager",
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
)

# Define tabs
maker_tab = dcc.Tab([survey_maker.survey_maker_layout()], label="Survey Maker")
taker_tab = dcc.Tab([survey_taker.survey_taker_layout()], label="Survey Taker")
analyzer_tab = dcc.Tab([survey_analyzer.survey_analyzer_layout()], label="Survey Analyzer")

# Main layout with tabs
app.layout = html.Div([
    html.H1("Survey Manager", style={
        "textAlign": "center",
        "marginBottom": "5px",
        "color": "#2c3e50",
    }),
    html.P("Build, distribute, and analyze surveys", style={
        "textAlign": "center",
        "color": "#7f8c8d",
        "marginTop": "0",
    }),
    dcc.Tabs(id="main-tabs", value="tab-maker", children=[
        maker_tab,
        taker_tab,
        analyzer_tab,
    ], style={
        "maxWidth": "1200px",
        "margin": "0 auto",
    }),
], style={"backgroundColor": "#ffffff"})


# ===== Survey Maker Callbacks =====

@callback(
    Output(cn.L_MAKER_SURVEY_SELECT, "options"),
    Input(cn.L_MAIN_TABS, cn.L_VALUE),
    prevent_initial_call=True,
)
def refresh_survey_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys]


@callback(
    Output(cn.L_MAKER_TITLE, cn.L_VALUE),
    Output(cn.L_MAKER_DESCRIPTION, cn.L_VALUE),
    Output(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN),
    Input(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    Input(cn.L_MAKER_CREATE_NEW, cn.L_N_CLICKS),
    prevent_initial_call=True,
)
def load_or_new_survey(survey_id, create_new_n):
    """Load an existing survey into the editor, or reset it for a new one."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == cn.L_MAKER_SURVEY_SELECT:
        if not survey_id:
            return "", "", []
        survey = load_survey(survey_id)
        if not survey:
            return "", "", []
        editors = [survey_maker.render_question_editor(q, q.id) for q in survey.questions]
        return survey.title, survey.description, editors

    if trigger_id == cn.L_MAKER_CREATE_NEW:
        editors = [survey_maker.render_question_editor(None, generate_id("q_"))]
        return "", "", editors

    return no_update, no_update, no_update


@callback(
    Output(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_MAKER_ADD_QUESTION, cn.L_N_CLICKS),
    State(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN),
    prevent_initial_call=True,
)
def add_question(n_clicks, current_children):
    """Append one new blank question editor, leaving existing ones untouched."""
    new_editor = survey_maker.render_question_editor(None, generate_id("q_"))
    return (current_children or []) + [new_editor]


@callback(
    Output(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN, allow_duplicate=True),
    Input({"type": "delete-q", "qid": ALL}, cn.L_N_CLICKS),
    State(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN),
    prevent_initial_call=True,
)
def delete_question(n_clicks_list, current_children):
    """Remove the question editor whose Delete button was actually clicked."""
    ctx = dash.callback_context
    triggered_value = ctx.triggered[0]["value"] if ctx.triggered else None
    qid = extract_clicked_qid(ctx.triggered_id, triggered_value)
    if qid is None:
        return no_update
    return remove_question_by_qid(current_children, qid)


@callback(
    Output({"type": "q-options-wrap", "qid": MATCH}, "style"),
    Output({"type": "q-scale-wrap", "qid": MATCH}, "style"),
    Output({"type": "q-matrix-wrap", "qid": MATCH}, "style"),
    Input({"type": "q-type", "qid": MATCH}, cn.L_VALUE),
)
def toggle_type_fields(type_value):
    """Show only the editor section relevant to the selected question type.

    Sections are never rebuilt, only shown/hidden, so switching a
    question's type can never discard already-entered options/scale/matrix
    data in the other sections.
    """
    visibility = type_visibility(type_value)
    return (
        section_style(visibility["options"]),
        section_style(visibility["scale"]),
        section_style(visibility["matrix"]),
    )


@callback(
    Output(cn.L_MAKER_STATUS, cn.L_CHILDREN),
    Output(cn.L_MAKER_SURVEY_SELECT, "options", allow_duplicate=True),
    Input(cn.L_MAKER_SAVE_SURVEY, "n_clicks"),
    State(cn.L_MAKER_TITLE, cn.L_VALUE),
    State(cn.L_MAKER_DESCRIPTION, cn.L_VALUE),
    State(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    State({"type": "q-type", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-type", "qid": ALL}, "id"),
    State({"type": "q-text", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-required", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-options", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-scale-min", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-scale-max", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-scale-label-min", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-scale-label-max", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-matrix-rows", "qid": ALL}, cn.L_VALUE),
    State({"type": "q-matrix-cols", "qid": ALL}, cn.L_VALUE),
    prevent_initial_call=True,
)
def save_survey_callback(n_clicks, title, description, selected_survey_id,
                          types, type_ids, texts, requireds, options_texts,
                          scale_mins, scale_maxs, scale_label_mins, scale_label_maxs,
                          matrix_rows_texts, matrix_cols_texts):
    """Save the current survey using the live values of the rendered form fields."""
    if not title:
        return html.Span("⚠️ Please enter a survey title.", style={"color": "orange"}), no_update

    qids = [d["qid"] for d in type_ids]
    if not qids:
        return html.Span("⚠️ No questions to save.", style={"color": "orange"}), no_update

    questions = assemble_questions_from_state(
        qids, types, texts, requireds, options_texts,
        scale_mins, scale_maxs, scale_label_mins, scale_label_maxs,
        matrix_rows_texts, matrix_cols_texts,
    )

    # Determine if we're editing an existing survey (selected in dropdown)
    if selected_survey_id and load_survey(selected_survey_id):
        survey_id = selected_survey_id
    else:
        survey_id = generate_id("srv_")

    survey = Survey(
        id=survey_id,
        title=title,
        description=description or "",
        questions=questions,
    )

    save_survey(survey)
    surveys = list_surveys()
    return (
        html.Span(f"✅ Survey '{title}' saved successfully!", style={"color": "green"}),
        [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys],
    )


@callback(
    Output(cn.L_MAKER_DELETE_CONFIRM, "displayed"),
    Output(cn.L_MAKER_DELETE_CONFIRM, "message"),
    Output(cn.L_MAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_MAKER_DELETE_SURVEY, cn.L_N_CLICKS),
    State(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    prevent_initial_call=True,
)
def confirm_delete_survey(n_clicks, survey_id):
    """Open the confirmation dialog for deleting the selected survey."""
    if not survey_id:
        return False, no_update, html.Span("⚠️ Select a survey to delete first.", style={"color": "orange"})

    survey = load_survey(survey_id)
    title = survey.title if survey else survey_id
    return True, f"Delete survey '{title}'? This cannot be undone.", no_update


@callback(
    Output(cn.L_MAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_MAKER_SURVEY_SELECT, "options", allow_duplicate=True),
    Output(cn.L_MAKER_TITLE, cn.L_VALUE, allow_duplicate=True),
    Output(cn.L_MAKER_DESCRIPTION, cn.L_VALUE, allow_duplicate=True),
    Output(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE, allow_duplicate=True),
    Input(cn.L_MAKER_DELETE_CONFIRM, "submit_n_clicks"),
    State(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    prevent_initial_call=True,
)
def perform_delete_survey(submit_n_clicks, survey_id):
    """Delete the selected survey (and its responses) once the user confirms."""
    delete_survey(survey_id)
    surveys = list_surveys()
    return (
        html.Span("✅ Survey deleted.", style={"color": "green"}),
        [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys],
        "",
        "",
        [],
        None,
    )


# ===== Survey Taker Callbacks =====

@callback(
    Output("taker-survey-select", "options"),
    Input("main-tabs", cn.L_VALUE),
    prevent_initial_call=True,
)
def refresh_taker_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys]


@callback(
    Output("taker-survey-form", cn.L_CHILDREN),
    Input("taker-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def show_survey(survey_id):
    """Render the form for the selected survey."""
    if not survey_id:
        return []

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found.")

    return [survey_taker.render_survey_taker(survey)]


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN),
    Input(cn.L_TAKER_SUBMIT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, "id"),
    prevent_initial_call=True,
)
def submit_survey_response(n_clicks, survey_id, values, ids):
    """Save the submitted answers as a Response.

    Registered once, statically, at import time (unlike the previous
    implementation, which tried to register this callback at request time
    inside `show_survey` — Dash never actually wires up a callback
    registered that way, so submissions were silently dropped).
    """
    if not survey_id:
        return html.Span("⚠️ No survey selected.", style={"color": "orange"})

    qids = [d["qid"] for d in ids]
    answers = build_response_answers_from_state(qids, values)

    response = Response(
        id=generate_id("resp_"),
        survey_id=survey_id,
        submitted_at=datetime.now().isoformat(),
        answers=answers,
    )
    save_response(response)

    return html.Span("✅ Thank you! Your response has been recorded.", style={"color": "green"})


@callback(
    Output("taker-survey-form", "style"),
    Output("taker-thankyou", "style"),
    Input("taker-submit", "n_clicks"),
    prevent_initial_call=True,
)
def show_thank_you(n_clicks):
    """Hide the form and show thank you message after submission."""
    if n_clicks == 0:
        return {}, {}
    return {"display": "none"}, {"display": "block"}


# ===== Survey Analyzer Callbacks =====

@callback(
    Output("analyzer-survey-select", "options"),
    Input("main-tabs", cn.L_VALUE),
    prevent_initial_call=True,
)
def refresh_analyzer_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys]


@callback(
    Output("analyzer-response-count", cn.L_CHILDREN),
    Output("analyzer-charts", cn.L_CHILDREN),
    Output("analyzer-data-table", "data"),
    Output("analyzer-data-table", "columns"),
    Input("analyzer-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def analyze_survey(survey_id):
    """Analyze survey responses and generate charts."""
    if not survey_id:
        return [], [], [], []

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found."), [], [], []

    responses = load_responses(survey_id)
    n_responses = len(responses)

    response_count = html.Div([
        html.H3(f"\"{survey.title}\""),
        html.P(f"Total responses: {n_responses}", style={"fontSize": "18px", "color": "#666"}),
    ])

    if n_responses == 0:
        return response_count, [html.P("No responses yet.")], [], []

    charts = []
    table_data = []

    for i, q in enumerate(survey.questions):
        fig = survey_analyzer._generate_question_chart(q, responses)
        if fig:
            charts.append(html.Div([
                html.H4(f"Q{i + 1}: {q.text}"),
                dcc.Graph(figure=fig),
                html.Hr(style={"marginTop": "20px", "marginBottom": "20px"}),
            ]))

    # Build table data
    headers = ["Response ID", "Submitted At"] + [
        f"Q{i+1}: {q.text[:30]}{'...' if len(q.text) > 30 else ''}"
        for i, q in enumerate(survey.questions)
    ]
    for resp in responses:
        row = {
            "Response ID": resp.id,
            "Submitted At": resp.submitted_at,
        }
        for q in survey.questions:
            answer = resp.answers.get(q.id, "")
            if isinstance(answer, list):
                answer = ", ".join(str(a) for a in answer)
            col_name = f"Q{survey.questions.index(q)+1}: {q.text[:30]}"
            row[col_name] = str(answer)
        table_data.append(row)

    return response_count, charts, table_data, [{"name": h, "id": h} for h in headers]


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8051)

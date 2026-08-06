"""Main Dash application for Survey Manager."""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Ensure src directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ALL
import dash

import survey_maker
import survey_taker
import survey_analyzer
from models import Question, Survey, Response, generate_id
from storage import save_survey, load_survey, list_surveys, save_response, load_responses


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

    # Hidden container for storing question data as JSON in textContent
    html.Div(id="maker-survey-data", children=json.dumps([]), style={"display": "none"}),
], style={"backgroundColor": "#ffffff"})


# ===== Survey Maker Callbacks =====

@callback(
    Output("maker-survey-select", "options"),
    Input("main-tabs", "value"),
    prevent_initial_call=True,
)
def refresh_survey_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], "value": s["id"]} for s in surveys]


@callback(
    Output("maker-title", "value"),
    Output("maker-description", "value"),
    Output("maker-questions-container", "children"),
    Output("maker-survey-data", "children"),
    Input("maker-survey-select", "value"),
    Input("maker-add-question", "n_clicks"),
    State("maker-title", "value"),
    State("maker-description", "value"),
    State("maker-survey-data", "children"),
    prevent_initial_call=True,
)
def handle_survey_load_or_add(survey_id, add_n, title, description, existing_data):
    """Handle both loading an existing survey and adding a new question.

    Uses callback_context to determine which input triggered the callback.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Loading an existing survey from dropdown
    if trigger_id == "maker-survey-select" and survey_id:
        survey = load_survey(survey_id)
        if not survey:
            return "", "", [], json.dumps([])

        editors = [survey_maker.render_question_editor(q, i) for i, q in enumerate(survey.questions)]
        q_data = [q.to_dict() for q in survey.questions]
        return survey.title, survey.description, editors, json.dumps(q_data)

    # Adding a new question via button click
    elif trigger_id == "maker-add-question":
        # Parse survey data - may be a JSON string from Store children
        raw = existing_data if existing_data else "[]"
        try:
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, list):
                data = raw
            else:
                data = []
        except (ValueError, TypeError):
            data = []
        n = len(data) + 1
        editors = [survey_maker.render_question_editor(None, i) for i in range(n)]
        new_q = Question(id=generate_id("q_"), type="text", text="", required=True).to_dict()
        data.append(new_q)
        return title or "", description or "", editors, json.dumps(data)

    # Default: no change
    return no_update, no_update, no_update, no_update


@callback(
    Output("maker-status", "children"),
    Input("maker-save-survey", "n_clicks"),
    State("maker-title", "value"),
    State("maker-description", "value"),
    State("maker-survey-data", "children"),
    prevent_initial_call=True,
)
def save_survey_callback(n_clicks, title, description, survey_data):
    """Save the current survey."""
    if not title:
        return html.Span("⚠️ Please enter a survey title.", style={"color": "orange"})

    if not survey_data:
        return html.Span("⚠️ No questions to save.", style={"color": "orange"})

    # Parse question data from store
    questions = [Question.from_dict(qd) for qd in survey_data]

    # Determine if we're editing an existing survey
    select_state = dash.callback_context.states[0].get("value") if dash.callback_context.states else None
    survey_id = ""
    if select_state:
        existing = load_survey(select_state)
        if existing:
            survey_id = select_state

    if not survey_id:
        survey_id = generate_id("srv_")

    survey = Survey(
        id=survey_id,
        title=title,
        description=description or "",
        questions=questions,
    )

    save_survey(survey)
    return html.Span(f"✅ Survey '{title}' saved successfully!", style={"color": "green"})


# ===== Survey Taker Callbacks =====

@callback(
    Output("taker-survey-select", "options"),
    Input("main-tabs", "value"),
    prevent_initial_call=True,
)
def refresh_taker_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], "value": s["id"]} for s in surveys]


@callback(
    Output("taker-survey-form", "children"),
    Input("taker-survey-select", "value"),
    prevent_initial_call=True,
)
def show_survey(survey_id):
    """Show the survey form when a survey is selected."""
    if not survey_id:
        return []

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found.")

    return [survey_taker.render_survey_taker(survey)]


@callback(
    Output("taker-status", "children"),
    Input("taker-submit", "n_clicks"),
    State("taker-survey-select", "value"),
    prevent_initial_call=True,
)
def submit_survey(n_clicks, survey_id):
    """Handle survey submission."""
    if not survey_id:
        return html.Span("⚠️ Please select a survey.", style={"color": "orange"})

    survey = load_survey(survey_id)
    if not survey:
        return html.Span("⚠️ Survey not found.", style={"color": "red"})

    # Collect answers from callback context states
    answers = {}
    for q in survey.questions:
        input_id = f"answer_{q.id}_value"
        answer_state = None
        for state in dash.callback_context.states:
            if isinstance(state, dict):
                sid = state.get("prop_id", "")
                if sid == input_id + ".value":
                    answer_state = state.get("value")
                    break

        if answer_state is not None:
            answers[q.id] = answer_state

    # Create and save response
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
    Input("main-tabs", "value"),
    prevent_initial_call=True,
)
def refresh_analyzer_list(tabs_value):
    """Refresh the survey dropdown when switching tabs."""
    surveys = list_surveys()
    return [{"label": s["title"], "value": s["id"]} for s in surveys]


@callback(
    Output("analyzer-response-count", "children"),
    Output("analyzer-charts", "children"),
    Output("analyzer-data-table", "data"),
    Output("analyzer-data-table", "columns"),
    Input("analyzer-survey-select", "value"),
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
    app.run(debug=True, host="0.0.0.0", port=8050)
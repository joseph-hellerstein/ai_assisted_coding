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
from models import Survey, Response, Draft, generate_id  # type: ignore
from storage import (  # type: ignore
    save_survey, load_survey, list_surveys, save_response, load_responses, delete_survey,
    delete_response, save_draft, load_draft, list_drafts, delete_draft,
)
from form_logic import (  # type: ignore
    type_visibility,
    section_style,
    extract_clicked_qid,
    assemble_questions_from_state,
    remove_question_by_qid,
    build_response_answers_from_state,
    draft_option_label,
)
from helpers import get_draft_info  # type: ignore


# ===== Create the app instance at module level so callbacks can register =====
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Survey Manager",
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
)

# Define tabs
_survey_titles = "\n".join(f"- {s['title']}" for s in list_surveys()) or "No surveys yet"
maker_tab = dcc.Tab(
    [survey_maker.survey_maker_layout()],
    label=html.Span(
        "Survey Maker",
        title=f"Available surveys:\n{_survey_titles}",
    ),
)

# The hover for this tab's label is populated live by refresh_taker_tab_hover
# below (keyed off which survey is selected in the Taker's own dropdown),
# not computed once here: that used to bake in whatever was true the moment
# the server process started, so it went stale the instant a draft was
# saved, resumed, or deleted during a running session.
taker_tab = dcc.Tab(
    [survey_taker.survey_taker_layout()],
    id=cn.L_TAKER_TAB,
    label=html.Span("Survey Taker", title="No current draft"),
)
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


def _taker_tab_label(survey_id):
    """The Survey Taker tab's own label, with a hover showing the
    "current" draft -- whichever survey is selected in the Taker's own
    dropdown right now, not a guess made once at server startup.
    """
    survey_title, completed, total, draft_count = get_draft_info(survey_id)
    if not survey_title:
        tooltip = "No current draft"
    else:
        tooltip = f"{survey_title}: {completed}/{total} answered"
        if draft_count > 1:
            tooltip += f" ({draft_count} drafts saved)"
    return html.Span("Survey Taker", title=tooltip)


@callback(
    Output(cn.L_TAKER_TAB, "label"),
    Input("main-tabs", cn.L_VALUE),
    Input("taker-survey-select", cn.L_VALUE),
)
def refresh_taker_tab_hover(tabs_value, survey_id):
    """Keep the Survey Taker tab's hover live.

    Refreshed on every tab switch and every survey selection change, and
    also re-set directly by save_draft_callback, delete_draft_callback,
    and submit_survey_response below (each saving/deleting/submitting a
    draft changes what this hover should say, without necessarily
    changing either of this callback's own Inputs). No
    prevent_initial_call here, deliberately: it should already be correct
    the moment the page loads, not just after the first interaction.
    """
    return _taker_tab_label(survey_id)


def _draft_options(survey_id):
    """Dropdown options for every saved draft of a survey, newest first."""
    return [
        {
            "label": draft_option_label(
                d["label"], d["saved_at"], d.get("questions_completed"), d.get("total_questions")
            ),
            cn.L_VALUE: d["id"],
        }
        for d in list_drafts(survey_id)
    ]


def _draft_section_style(has_drafts: bool) -> dict:
    """Show/hide the whole "Resume a saved draft" control: there's nothing
    useful to show it for once the survey (or its last draft) has none."""
    return {"display": "block"} if has_drafts else {"display": "none"}


@callback(
    Output(cn.L_TAKER_DRAFT_SELECT, "options"),
    Output(cn.L_TAKER_DRAFT_SECTION, "style"),
    Input("taker-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def refresh_draft_list(survey_id):
    """Refresh the resume-draft dropdown when the chosen survey changes."""
    if not survey_id:
        return [], _draft_section_style(False)
    options = _draft_options(survey_id)
    return options, _draft_section_style(bool(options))


@callback(
    Output("taker-survey-form", cn.L_CHILDREN),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    Output(cn.L_TAKER_DRAFT_LABEL, cn.L_VALUE),
    Input("taker-survey-select", cn.L_VALUE),
    Input(cn.L_TAKER_DRAFT_SELECT, cn.L_VALUE),
    prevent_initial_call=True,
)
def show_survey(survey_id, draft_id):
    """Render the form for the selected survey, resuming a draft if one was picked."""
    if not survey_id:
        return [], None, ""

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found."), None, ""

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if trigger_id == cn.L_TAKER_DRAFT_SELECT and draft_id:
        draft = load_draft(survey_id, draft_id)
        if draft:
            return [survey_taker.render_survey_taker(survey, initial_answers=draft.answers)], draft.id, draft.label

    return [survey_taker.render_survey_taker(survey)], None, ""


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SELECT, "options", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SELECT, cn.L_VALUE, allow_duplicate=True),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB, "label", allow_duplicate=True),
    Input(cn.L_TAKER_SAVE_DRAFT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State(cn.L_TAKER_DRAFT_LABEL, cn.L_VALUE),
    State(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    State({"type": "answer", "qid": ALL}, cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, "id"),
    prevent_initial_call=True,
)
def save_draft_callback(n_clicks, survey_id, label, current_draft_id, values, ids):
    """Save the live, possibly-incomplete answers as a resumable Draft.

    Reuses `current_draft_id` only when it was already set -- i.e. only
    when this save is a continuation of a draft the user explicitly loaded
    via the resume dropdown (show_survey is what sets it). A "fresh"
    session (nothing resumed, current_draft_id is None) always gets a new
    draft id, and the Store is deliberately left untouched (no_update)
    rather than adopting it: otherwise the *next*, unrelated Save for
    Later click in that same fresh session would silently start reusing
    (and overwriting) this one instead of creating its own draft. Every
    survey can accumulate any number of such drafts; the resume dropdown
    lists all of them.
    """
    if not survey_id:
        return (
            html.Span("⚠️ Select a survey first.", style={"color": "orange"}),
            no_update, no_update, no_update, no_update, no_update,
        )

    qids = [d["qid"] for d in ids]
    answers = build_response_answers_from_state(qids, values)

    draft_id = current_draft_id or generate_id("draft_")
    draft = Draft(
        id=draft_id,
        survey_id=survey_id,
        label=label or "",
        saved_at=datetime.now().isoformat(),
        answers=answers,
    )
    save_draft(draft)

    # The draft dropdown's *value* is deliberately left untouched (no_update):
    # selecting it would itself be an Input to show_survey, which would
    # immediately rebuild the form and wipe this very status message.
    updated_current_draft_id = draft_id if current_draft_id else no_update

    return (
        html.Span("✅ Progress saved. Resume it later from the dropdown above.", style={"color": "green"}),
        _draft_options(survey_id),
        no_update,
        updated_current_draft_id,
        _draft_section_style(True),  # a draft now definitely exists for this survey
        _taker_tab_label(survey_id),
    )


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output("taker-survey-form", cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB, "label", allow_duplicate=True),
    Input(cn.L_TAKER_DELETE_DRAFT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    prevent_initial_call=True,
)
def delete_draft_callback(n_clicks, survey_id, current_draft_id):
    """Delete whichever draft is currently loaded, and reset the form to
    blank -- the deleted draft's answers shouldn't linger on screen.

    Rebuilds "taker-survey-form" directly here (rather than clearing the
    draft dropdown's value and letting show_survey react to that) so a
    status message survives: changing the dropdown's own options/value
    would cascade into show_survey anyway, but *as its own trigger*, which
    would wipe whatever this callback just set. The "Draft deleted."
    message is baked into that same render call (render_survey_taker's
    `status_message`) rather than sent as a separate Output to the nested
    "taker-status" div -- Dash applies one callback's Outputs in
    declaration order, so a later whole-form-rebuild Output would just
    overwrite an earlier, separate status Output with the status div's own
    (empty) default. The dropdown itself is left stale and self-corrects
    next time the survey is reselected.
    """
    if not survey_id or not current_draft_id:
        return (
            html.Span("⚠️ No draft selected to delete.", style={"color": "orange"}),
            no_update, no_update, no_update, no_update,
        )

    delete_draft(survey_id, current_draft_id)
    section_style = _draft_section_style(bool(list_drafts(survey_id)))

    survey = load_survey(survey_id)
    blank_form = (
        [survey_taker.render_survey_taker(survey, status_message="✅ Draft deleted.")]
        if survey else no_update
    )

    return (
        no_update,
        blank_form,
        None,
        section_style,
        _taker_tab_label(survey_id),
    )


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB, "label", allow_duplicate=True),
    Input(cn.L_TAKER_SUBMIT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, "id"),
    State(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    prevent_initial_call=True,
)
def submit_survey_response(n_clicks, survey_id, values, ids, current_draft_id):
    """Save the submitted answers as a Response.

    Registered once, statically, at import time (unlike the previous
    implementation, which tried to register this callback at request time
    inside `show_survey` — Dash never actually wires up a callback
    registered that way, so submissions were silently dropped).

    If this submission resumed a saved draft, that draft is deleted once
    it becomes a real response, so it stops showing up as resumable. The
    draft dropdown's *options* are deliberately left stale here (they'll
    naturally refresh next time the survey is reselected) rather than
    updated inline: removing the just-submitted draft from the options
    would clear the dropdown's own *value* client-side (its selected
    option no longer existing), which would be a genuine prop change that
    re-triggers show_survey — rebuilding the form and wiping this very
    "Thank you" message. The resume section's *style* is safe to update
    directly, though: it's a different component than the dropdown and
    isn't anyone's Input, so toggling it can't trigger that cascade.

    The `if not n_clicks` guard matters here specifically because this
    callback (unlike before) now also writes to components that already
    exist outside the dynamically-rendered form (the draft-id Store, the
    resume section): Dash fires a callback like that once, spuriously, at
    n_clicks=0 the moment its dynamically-mounted Input component (the
    Submit button, recreated by show_survey on every survey/draft
    selection) first appears — the existing show_thank_you callback below
    already guards against the exact same quirk for that reason.
    """
    if not n_clicks:
        return no_update, no_update, no_update, no_update
    if not survey_id:
        return html.Span("⚠️ No survey selected.", style={"color": "orange"}), no_update, no_update, no_update

    qids = [d["qid"] for d in ids]
    answers = build_response_answers_from_state(qids, values)

    response = Response(
        id=generate_id("resp_"),
        survey_id=survey_id,
        submitted_at=datetime.now().isoformat(),
        answers=answers,
    )
    save_response(response)

    cleared_draft_id = no_update
    section_style = no_update
    if current_draft_id:
        delete_draft(survey_id, current_draft_id)
        cleared_draft_id = None
        section_style = _draft_section_style(bool(list_drafts(survey_id)))

    return (
        html.Span("✅ Thank you! Your response has been recorded.", style={"color": "green"}),
        cleared_draft_id,
        section_style,
        _taker_tab_label(survey_id),
    )


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


def _response_count_and_charts(survey, responses):
    """The response-count summary + per-question charts for the Analyzer.

    Shared by the initial analyze_survey render and delete_response_row (so
    deleting a response refreshes the same summary/charts without
    duplicating this logic).
    """
    n_responses = len(responses)

    response_count = html.Div([
        html.H3(f"\"{survey.title}\""),
        html.P(f"Total responses: {n_responses}", style={"fontSize": "18px", "color": "#666"}),
    ])

    if n_responses == 0:
        return response_count, [html.P("No responses yet.")]

    charts = []
    for i, q in enumerate(survey.questions):
        fig = survey_analyzer._generate_question_chart(q, responses)
        if fig:
            charts.append(html.Div([
                html.H4(f"Q{i + 1}: {q.text}"),
                dcc.Graph(figure=fig),
                html.Hr(style={"marginTop": "20px", "marginBottom": "20px"}),
            ]))

    return response_count, charts


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
    response_count, charts = _response_count_and_charts(survey, responses)

    if not responses:
        return response_count, charts, [], []

    table_data = []

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


@callback(
    Output("analyzer-response-count", cn.L_CHILDREN, allow_duplicate=True),
    Output("analyzer-charts", cn.L_CHILDREN, allow_duplicate=True),
    Input("analyzer-data-table", "data"),
    State("analyzer-data-table", "data_previous"),
    State("analyzer-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def delete_response_row(data, data_previous, survey_id):
    """Persist a row removed via the raw-data table's built-in delete ("x")
    control as an actual deletion, and refresh the dependent summary/charts.

    Guarded to fire only for a genuine single-row deletion -- exactly one
    fewer row, and every remaining id already present before -- rather than
    every "data" change: selecting a different survey also rewrites "data"
    (via analyze_survey), and without this guard would be misread as
    deleting every response that belonged to the previously-shown survey.
    """
    if not survey_id or not data_previous or len(data) != len(data_previous) - 1:
        return no_update, no_update

    previous_ids = {row["Response ID"] for row in data_previous}
    current_ids = {row["Response ID"] for row in data}
    removed_ids = previous_ids - current_ids
    if len(removed_ids) != 1 or not current_ids <= previous_ids:
        return no_update, no_update

    delete_response(next(iter(removed_ids)), survey_id)

    survey = load_survey(survey_id)
    if not survey:
        return no_update, no_update

    return _response_count_and_charts(survey, load_responses(survey_id))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8051)

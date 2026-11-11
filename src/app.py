"""Main Dash application for Survey Manager."""

from datetime import datetime
from dash import Dash, dcc, html, Input, Output, State, callback, no_update, ALL, MATCH
import dash
import os
import time

import src.survey_maker  as survey_maker # type: ignore
import src.survey_taker as survey_taker  # type: ignore
import src.survey_analyzer as survey_analyzer  # type: ignore
from src import shelpers
import src.constants as cn  # type: ignore
from src.models import Survey, Response, Draft, generate_id  # type: ignore
from src.storage import (  # type: ignore
    save_survey, load_survey, list_surveys, save_response, load_responses, delete_survey,
    delete_response, save_draft, load_draft, list_drafts, delete_draft,
)
from src.form_logic import (  # type: ignore
    type_visibility,
    section_style,
    extract_clicked_qid,
    assemble_questions_from_state,
    remove_question_by_qid,
    build_response_answers_from_state,
    draft_option_label,
    is_valid_respondent_id,
)
from src.shelpers import get_draft_info  # type: ignore
import src.sample_data as sample_data  # type: ignore


PORT = 8051


# ===== Create the app instance at module level so callbacks can register =====
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Survey Manager",
    assets_folder=os.path.join(os.path.dirname(__file__), "assets"),
)

# The tab buttons' hover tooltips (see maker_tab_tooltip etc. below) are
# shown/hidden with a plain CSS :hover rule, no JavaScript. That CSS used to
# live in assets/tooltip.css, loaded via a <link rel="stylesheet">, but an
# embedded/in-app browser pane rendering a snapshot of the page didn't
# follow that second request -- the tooltip divs stayed permanently visible
# because their `display: none` default never arrived. Inlining the rule
# into the page's own <head> via index_string ships it with the initial
# HTML itself, so there's nothing extra to fetch.
app.index_string = app.index_string.replace(
    "{%css%}",
    "{%css%}\n        <style>\n"
    "            .tab-with-tooltip { position: relative; display: inline-block; }\n"
    "            .tab-tooltip {\n"
    "                display: none;\n"
    "                position: absolute;\n"
    "                top: 100%;\n"
    "                left: 50%;\n"
    "                transform: translateX(-50%);\n"
    "                margin-top: 6px;\n"
    "                padding: 12px 18px;\n"
    "                background-color: #2c3e50;\n"
    "                color: #ffffff;\n"
    "                border-radius: 4px;\n"
    "                font-size: 15.5px;\n"
    "                font-weight: normal;\n"
    "                line-height: 1.4;\n"
    "                white-space: pre-line;\n"
    "                text-align: left;\n"
    "                z-index: 1000;\n"
    "                min-width: 330px;\n"
    "                max-width: 480px;\n"
    "                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);\n"
    "            }\n"
    "            .tab-with-tooltip:hover .tab-tooltip { display: block; }\n"
    "        </style>",
)

# Define tabs
#
# These used to be dcc.Tabs/dcc.Tab, which only ever fires a callback when
# the *selected* tab changes -- clicking the already-active tab again
# doesn't change anything, so there's no event to detect that second
# click. To support "click again to collapse" (see toggle_active_tab
# below), the tab bar is three plain buttons instead, each toggling a
# dcc.Store that tracks which one (if any) is currently open; a second
# callback (render_active_tab) reflects that Store onto each button's
# highlighted state and each content area's visibility.
TAB_MAKER = "tab-maker"
TAB_TAKER = "tab-taker"
TAB_ANALYZER = "tab-analyzer"

_TAB_BUTTON_TO_VALUE = {
    cn.L_MAKER_TAB: TAB_MAKER,
    cn.L_TAKER_TAB: TAB_TAKER,
    cn.L_ANALYZER_TAB: TAB_ANALYZER,
}


def _tab_button_style(is_active):
    """Visual state for one of the three main tab buttons -- highlighted
    when its content is the one currently showing, flat otherwise."""
    return {
        "padding": "10px 24px",
        "border": "none",
        "borderBottom": "3px solid #4CAF50" if is_active else "3px solid transparent",
        "backgroundColor": "#ffffff",
        "fontWeight": "bold" if is_active else "normal",
        "color": "#2c3e50" if is_active else "#7f8c8d",
        "cursor": "pointer",
        "fontSize": "18px",
    }


def _maker_tab_label():
    """The Survey Maker tab button's own hover, listing every saved
    survey. Recomputed live by refresh_maker_tab_hover below (and
    re-set directly by generate_test_data/delete_all_test_data/
    save_survey_callback/perform_delete_survey), not computed once here:
    that used to bake in whatever surveys existed the moment the server
    process started, so a survey created afterward (by hand, or via the
    "Test" panel) never showed up without restarting the app.
    """
    surveys = list_surveys()
    survey_titles = "\n".join(f"- {s['title']}" for s in surveys) or "No surveys yet"
    return f"Available surveys:\n{survey_titles}"


def _taker_tab_label():
    """The Survey Taker tab button's own hover, listing every saved
    survey's drafts. Recomputed live by refresh_taker_tab_hover below (and
    re-set directly by save_draft_callback/delete_draft_callback/
    submit_survey_response/generate_test_data/delete_all_test_data/
    perform_delete_survey), not computed once at server startup -- that
    used to bake in whatever was true the moment the process started, so
    it went stale the instant a draft was saved, resumed, or deleted
    during a running session. It also used to only ever describe
    whichever one survey was selected in the Taker's own dropdown, so a
    draft belonging to any *other* survey never showed up here at all.
    """
    lines = []
    surveys = shelpers.sort_surveys_by_title(list_surveys())  # sort by title for a more predictable hover order
    for info in surveys:
        title, completed, total, draft_count = get_draft_info(info["id"])
        if draft_count == 0:
            lines.append(f"{info['title']}: no drafts")
        elif draft_count == 1:
            lines.append(f"{title}: 1 draft ({completed}/{total} answered)")
        else:
            lines.append(f"{title}: {draft_count} drafts (newest {completed}/{total} answered)")
    body = "\n".join(lines) or "No surveys yet"
    return f"Drafts by survey:\n{body}"


def _analyzer_tab_label():
    """The Survey Analyzer tab button's own hover, listing every saved
    survey's response count. Recomputed live by
    refresh_analyzer_tab_hover below (and re-set directly wherever a
    response is created/deleted or a survey is deleted), mirroring
    _taker_tab_label/_maker_tab_label above.
    """
    lines = []
    for info in list_surveys():
        n = len(load_responses(info["id"]))
        lines.append(f"- {info['title']}: {n} response{'s' if n != 1 else ''}")
    body = "\n".join(lines) or "No surveys yet"
    return f"Responses by survey:\n{body}"


maker_tab_button = html.Button(
    "Survey Maker", id=cn.L_MAKER_TAB,
    n_clicks=0, style=_tab_button_style(True),
)
taker_tab_button = html.Button(
    "Survey Taker", id=cn.L_TAKER_TAB,
    n_clicks=0, style=_tab_button_style(False),
)
analyzer_tab_button = html.Button(
    "Survey Analyzer", id=cn.L_ANALYZER_TAB,
    n_clicks=0, style=_tab_button_style(False),
)

# Each tab button's hover info used to live in its native `title` attribute,
# but that's a browser-chrome feature: embedded/in-app browser panes render
# the page fine but don't implement the native tooltip popup, so the text
# was there in the DOM and simply never appeared on screen. These sibling
# divs (shown via the pure-CSS :hover rule in assets/tooltip.css, no
# JavaScript) render the same text as part of the page itself instead, so
# it works regardless of what's hosting the browser view.
maker_tab_tooltip = html.Div(_maker_tab_label(), id=cn.L_MAKER_TAB_TOOLTIP, className="tab-tooltip")
taker_tab_tooltip = html.Div(_taker_tab_label(), id=cn.L_TAKER_TAB_TOOLTIP, className="tab-tooltip")
analyzer_tab_tooltip = html.Div(_analyzer_tab_label(), id=cn.L_ANALYZER_TAB_TOOLTIP, className="tab-tooltip")

maker_tab_button_wrap = html.Div([maker_tab_button, maker_tab_tooltip], className="tab-with-tooltip")
taker_tab_button_wrap = html.Div([taker_tab_button, taker_tab_tooltip], className="tab-with-tooltip")
analyzer_tab_button_wrap = html.Div([analyzer_tab_button, analyzer_tab_tooltip], className="tab-with-tooltip")

maker_tab = html.Div([survey_maker.survey_maker_layout()],
                      id=cn.L_MAKER_CONTENT, style={"display": "block"})
taker_tab = html.Div([survey_taker.survey_taker_layout()],
                      id=cn.L_TAKER_CONTENT, style={"display": "none"})
analyzer_tab = html.Div([survey_analyzer.survey_analyzer_layout()],
                         id=cn.L_ANALYZER_CONTENT, style={"display": "none"})

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

    # Dev/demo utility: generate (or wipe) throwaway sample data without
    # building a survey by hand. Lives in the same storage as real
    # surveys/responses/drafts -- see src/sample_data.py.
    html.Div([
        html.Button("🧪 Test", id=cn.L_TEST_TOGGLE, n_clicks=0, style={
            "fontSize": "12px",
            "padding": "4px 10px",
            "backgroundColor": "#f5f5f5",
            "border": "1px solid #ccc",
            "borderRadius": "4px",
            "cursor": "pointer",
        }),
        html.Div([
            html.Div([
                html.Label("# completed responses:", style={"marginRight": "8px"}),
                dcc.Input(id=cn.L_TEST_N_COMPLETED, type="number", min=0, value=3,
                          style={"width": "70px", "marginRight": "20px"}),
                html.Label("# draft responses:", style={"marginRight": "8px"}),
                dcc.Input(id=cn.L_TEST_N_DRAFTS, type="number", min=0, value=1,
                          style={"width": "70px"}),
            ], style={"marginBottom": "10px"}),
            html.Button("Generate Random Survey", id=cn.L_TEST_GENERATE, n_clicks=0,
                        style={"marginRight": "10px"}),
            html.Button("Delete All Test Data", id=cn.L_TEST_DELETE_ALL, n_clicks=0),
            html.Div(id=cn.L_TEST_STATUS, style={"marginTop": "8px", "fontWeight": "bold"}),
        ], id=cn.L_TEST_PANEL, style={
            "display": "none",
            "maxWidth": "600px",
            "margin": "10px auto",
            "padding": "12px",
            "border": "1px dashed #ccc",
            "borderRadius": "6px",
            "backgroundColor": "#fafafa",
        }),
    ], style={"textAlign": "center", "marginBottom": "10px"}),

    dcc.Store(id=cn.L_ACTIVE_TAB_STORE, data=TAB_MAKER),
    html.Div([
        maker_tab_button_wrap,
        taker_tab_button_wrap,
        analyzer_tab_button_wrap,
    ], id="main-tabs", style={
        "maxWidth": "1200px",
        "margin": "0 auto",
        "textAlign": "center",
        "borderBottom": "1px solid #ddd",
        "marginBottom": "20px",
    }),
    maker_tab,
    taker_tab,
    analyzer_tab,
], style={"backgroundColor": "#ffffff"})


@callback(
    Output(cn.L_ACTIVE_TAB_STORE, "data"),
    Input(cn.L_MAKER_TAB, cn.L_N_CLICKS),
    Input(cn.L_TAKER_TAB, cn.L_N_CLICKS),
    Input(cn.L_ANALYZER_TAB, cn.L_N_CLICKS),
    State(cn.L_ACTIVE_TAB_STORE, "data"),
    prevent_initial_call=True,
)
def toggle_active_tab(maker_clicks, taker_clicks, analyzer_clicks, current_active):
    """Clicking the currently-open tab's button again collapses it (no
    tab shown); clicking a different one switches to it normally -- the
    same toggle pattern as the "Test" panel's own button (see
    toggle_test_panel below), just applied to all three main tabs.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    clicked_tab = _TAB_BUTTON_TO_VALUE.get(triggered_id)
    if clicked_tab is None:
        return no_update
    return None if clicked_tab == current_active else clicked_tab


@callback(
    Output(cn.L_MAKER_TAB, "style"),
    Output(cn.L_TAKER_TAB, "style"),
    Output(cn.L_ANALYZER_TAB, "style"),
    Output(cn.L_MAKER_CONTENT, "style"),
    Output(cn.L_TAKER_CONTENT, "style"),
    Output(cn.L_ANALYZER_CONTENT, "style"),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def render_active_tab(active_tab):
    """Reflect the active-tab Store onto the three buttons' highlighted
    state and the three content areas' visibility. No prevent_initial_call:
    it should already match the Store's own initial data the moment the
    page loads.
    """
    return (
        _tab_button_style(active_tab == TAB_MAKER),
        _tab_button_style(active_tab == TAB_TAKER),
        _tab_button_style(active_tab == TAB_ANALYZER),
        {"display": "block" if active_tab == TAB_MAKER else "none"},
        {"display": "block" if active_tab == TAB_TAKER else "none"},
        {"display": "block" if active_tab == TAB_ANALYZER else "none"},
    )


# ===== Test-data Callbacks =====

@callback(
    Output(cn.L_TEST_PANEL, "style"),
    Input(cn.L_TEST_TOGGLE, cn.L_N_CLICKS),
    State(cn.L_TEST_PANEL, "style"),
    prevent_initial_call=True,
)
def toggle_test_panel(n_clicks, current_style):
    """Show/hide the test-data panel; it starts collapsed (see layout)."""
    is_open = (current_style or {}).get("display") != "none"
    new_style = dict(current_style or {})
    new_style["display"] = "none" if is_open else "block"
    return new_style


@callback(
    Output(cn.L_TEST_STATUS, cn.L_CHILDREN),
    Output(cn.L_MAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_TEST_GENERATE, cn.L_N_CLICKS),
    State(cn.L_TEST_N_COMPLETED, cn.L_VALUE),
    State(cn.L_TEST_N_DRAFTS, cn.L_VALUE),
    prevent_initial_call=True,
)
def generate_test_data(n_clicks, n_completed, n_drafts):
    """Generate one new random survey plus the requested number of
    completed/draft responses for it (src/sample_data.py). Saved through
    the normal storage functions, so it lives alongside real user data.

    Also refreshes all three tabs' hovers directly (rather than waiting
    for a tab switch): the new survey affects Maker's list, and the new
    drafts/responses affect Taker's and Analyzer's.
    """
    try:
        n_completed = int(n_completed)
        n_drafts = int(n_drafts)
    except (TypeError, ValueError):
        return (
            html.Span("⚠️ Enter whole numbers for both counts.", style={"color": "orange"}),
            no_update, no_update, no_update,
        )
    if n_completed < 0 or n_drafts < 0:
        return (
            html.Span("⚠️ Counts must be zero or more.", style={"color": "orange"}),
            no_update, no_update, no_update,
        )

    survey = sample_data.generate_random_survey()
    sample_data.generate_random_responses(survey, n_completed, n_drafts)
    return (
        html.Span(
            f"✅ Created \"{survey.title}\" with {n_completed} completed and "
            f"{n_drafts} draft response(s).",
            style={"color": "green"},
        ),
        _maker_tab_label(),
        _taker_tab_label(),
        _analyzer_tab_label(),
    )


@callback(
    Output(cn.L_TEST_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_MAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_TEST_DELETE_ALL, cn.L_N_CLICKS),
    prevent_initial_call=True,
)
def delete_all_test_data(n_clicks):
    """Delete every randomly generated survey (and its responses/drafts),
    leaving any real user-created surveys untouched; also refreshes all
    three tabs' hovers directly, same reasoning as generate_test_data.
    """
    count = sample_data.delete_all_generated_data()
    return (
        html.Span(
            f"✅ Deleted {count} randomly generated survey(s) and their responses/drafts.",
            style={"color": "green"},
        ),
        _maker_tab_label(),
        _taker_tab_label(),
        _analyzer_tab_label(),
    )


# ===== Survey Maker Callbacks =====

@callback(
    Output(cn.L_MAKER_TAB_TOOLTIP, cn.L_CHILDREN),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_maker_tab_hover(tabs_value):
    """Keep the Survey Maker tab's hover live; see _maker_tab_label above.

    No prevent_initial_call: it should already be correct the moment the
    page loads, not just after the first tab switch.
    """
    return _maker_tab_label()


@callback(
    Output(cn.L_MAKER_SURVEY_SELECT, "options"),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_survey_list(tabs_value):
    """Refresh the survey dropdown when switching tabs. No
    prevent_initial_call: it should already be populated the moment the
    page loads (Maker is the default-active tab, so without this the
    dropdown stayed empty until the user switched tabs away and back).
    """
    surveys = list_surveys()
    return [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys]


@callback(
    Output(cn.L_MAKER_TITLE, cn.L_VALUE),
    Output(cn.L_MAKER_DESCRIPTION, cn.L_VALUE),
    Output(cn.L_MAKER_QUESTIONS_CONTAINER, cn.L_CHILDREN),
    Output(cn.L_MAKER_EDITOR_SECTION, "style"),
    Input(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    Input(cn.L_MAKER_CREATE_NEW, cn.L_N_CLICKS),
    prevent_initial_call=True,
)
def load_or_new_survey(survey_id, create_new_n):
    """Load an existing survey into the editor, or reset it for a new one.

    The editor section (title/description/questions/save-survey) is hidden
    until this fires with something to actually edit -- see
    survey_maker.survey_maker_layout, where it starts hidden.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == cn.L_MAKER_SURVEY_SELECT:
        if not survey_id:
            return "", "", [], {"display": "none"}
        survey = load_survey(survey_id)
        if not survey:
            return "", "", [], {"display": "none"}
        editors = [survey_maker.render_question_editor(q, q.id) for q in survey.questions]
        return survey.title, survey.description, editors, {"display": "block"}

    if trigger_id == cn.L_MAKER_CREATE_NEW:
        editors = [survey_maker.render_question_editor(None, generate_id("q_"))]
        return "", "", editors, {"display": "block"}

    return no_update, no_update, no_update, no_update


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
    Output(cn.L_MAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
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
        return html.Span("⚠️ Please enter a survey title.", style={"color": "orange"}), no_update, no_update

    qids = [d["qid"] for d in type_ids]
    if not qids:
        return html.Span("⚠️ No questions to save.", style={"color": "orange"}), no_update, no_update

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
        _maker_tab_label(),
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
    Output(cn.L_MAKER_EDITOR_SECTION, "style", allow_duplicate=True),
    Output(cn.L_MAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_MAKER_DELETE_CONFIRM, "submit_n_clicks"),
    State(cn.L_MAKER_SURVEY_SELECT, cn.L_VALUE),
    prevent_initial_call=True,
)
def perform_delete_survey(submit_n_clicks, survey_id):
    """Delete the selected survey (and its responses) once the user
    confirms; also refreshes all three tabs' hovers directly, since the
    deleted survey (and whatever drafts/responses it had) should
    disappear from each of their listings right away. The editor section
    is hidden again too, same reasoning as load_or_new_survey: nothing
    left to edit once the dropdown is cleared."""
    delete_survey(survey_id)
    surveys = list_surveys()
    return (
        html.Span("✅ Survey deleted.", style={"color": "green"}),
        [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys],
        "",
        "",
        [],
        None,
        {"display": "none"},
        _maker_tab_label(),
        _taker_tab_label(),
        _analyzer_tab_label(),
    )


# ===== Survey Taker Callbacks =====

@callback(
    Output("taker-survey-select", "options"),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_taker_list(tabs_value):
    """Refresh the survey dropdown when switching tabs. No
    prevent_initial_call: see refresh_survey_list above -- it should
    already be populated the moment the page loads.
    """
    surveys = list_surveys()
    return [{"label": s["title"], cn.L_VALUE: s["id"]} for s in surveys]


@callback(
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_taker_tab_hover(tabs_value):
    """Keep the Survey Taker tab's hover live; see _taker_tab_label above.

    Refreshed on every tab switch, and also re-set directly by
    save_draft_callback/delete_draft_callback/submit_survey_response/
    generate_test_data/delete_all_test_data/perform_delete_survey below
    (each changes what this hover should say, without necessarily
    changing this callback's own Input). No prevent_initial_call,
    deliberately: it should already be correct the moment the page
    loads, not just after the first tab switch.
    """
    return _taker_tab_label()


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
    Output(cn.L_TAKER_DRAFT_CONTROLS, "style"),
    Input("taker-survey-select", cn.L_VALUE),
    Input(cn.L_TAKER_DRAFT_SELECT, cn.L_VALUE),
    prevent_initial_call=True,
)
def show_survey(survey_id, draft_id):
    """Render the form for the selected survey, resuming a draft if one was
    picked. The "Save for Later" / "Delete This Draft" controls are hidden
    until a survey is actually chosen -- see survey_taker.survey_taker_layout,
    where that section starts hidden.
    """
    if not survey_id:
        return [], None, "", {"display": "none"}

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found."), None, "", {"display": "none"}

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if trigger_id == cn.L_TAKER_DRAFT_SELECT and draft_id:
        draft = load_draft(survey_id, draft_id)
        if draft:
            return (
                [survey_taker.render_survey_taker(
                    survey, initial_answers=draft.answers, initial_respondent_id=draft.respondent_id,
                )],
                draft.id, draft.label, {"textAlign": "center", "marginTop": "10px"},
            )

    return [survey_taker.render_survey_taker(survey)], None, "", {"textAlign": "center", "marginTop": "10px"}


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SELECT, "options", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SELECT, cn.L_VALUE, allow_duplicate=True),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_TAKER_SAVE_DRAFT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State(cn.L_TAKER_DRAFT_LABEL, cn.L_VALUE),
    State(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    State({"type": "answer", "qid": ALL}, cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, "id"),
    State(cn.L_TAKER_RESPONDENT_ID, cn.L_VALUE),
    prevent_initial_call=True,
)
def save_draft_callback(n_clicks, survey_id, label, current_draft_id, values, ids, respondent_id):
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
        respondent_id=respondent_id or "",
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
        _taker_tab_label(),
    )


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN, allow_duplicate=True),
    Output("taker-survey-form", cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
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
        _taker_tab_label(),
    )


@callback(
    Output(cn.L_TAKER_STATUS, cn.L_CHILDREN),
    Output(cn.L_TAKER_CURRENT_DRAFT_STORE, "data", allow_duplicate=True),
    Output(cn.L_TAKER_DRAFT_SECTION, "style", allow_duplicate=True),
    Output(cn.L_TAKER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input(cn.L_TAKER_SUBMIT, "n_clicks"),
    State("taker-survey-select", cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, cn.L_VALUE),
    State({"type": "answer", "qid": ALL}, "id"),
    State(cn.L_TAKER_CURRENT_DRAFT_STORE, "data"),
    State(cn.L_TAKER_RESPONDENT_ID, cn.L_VALUE),
    prevent_initial_call=True,
)
def submit_survey_response(n_clicks, survey_id, values, ids, current_draft_id, respondent_id):
    """Save the submitted answers as a Response.

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
        return no_update, no_update, no_update, no_update, no_update
    if not survey_id:
        return (
            html.Span("⚠️ No survey selected.", style={"color": "orange"}),
            no_update, no_update, no_update, no_update,
        )
    if not is_valid_respondent_id(respondent_id):
        return (
            html.Span("⚠️ Your ID must be exactly 5 digits.", style={"color": "orange"}),
            no_update, no_update, no_update, no_update,
        )
    if has_duplicate_respondent_id(survey_id, respondent_id):
        return (
            html.Span("⚠️ This ID has already been used for this survey.", style={"color": "orange"}),
            no_update, no_update, no_update, no_update,
        )

    qids = [d["qid"] for d in ids]
    answers = build_response_answers_from_state(qids, values)

    response = Response(
        id=generate_id("resp_"),
        survey_id=survey_id,
        submitted_at=datetime.now().isoformat(),
        answers=answers,
        respondent_id=respondent_id,
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
        _taker_tab_label(),
        _analyzer_tab_label(),
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


@callback(
    Output("taker-survey-select", cn.L_VALUE, allow_duplicate=True),
    Output("taker-survey-form", "style", allow_duplicate=True),
    Output("taker-thankyou", "style", allow_duplicate=True),
    Input(cn.L_TAKER_TAKE_ANOTHER, cn.L_N_CLICKS),
    prevent_initial_call=True,
)
def take_another_survey(n_clicks):
    """Leave the "Thank you" screen and return to picking a survey, without
    needing to switch tabs away and back first.

    Clearing the survey dropdown's value is enough: it's show_survey's own
    Input, so that callback reacts on its own and empties/hides everything
    downstream (the form, the resume-draft section) exactly as it would if
    the respondent had cleared the dropdown themselves.
    """
    if not n_clicks:
        return no_update, no_update, no_update
    return None, {}, {"display": "none"}


# ===== Survey Analyzer Callbacks =====

@callback(
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_analyzer_tab_hover(tabs_value):
    """Keep the Survey Analyzer tab's hover live; see _analyzer_tab_label
    above. No prevent_initial_call, same reasoning as
    refresh_taker_tab_hover/refresh_maker_tab_hover.
    """
    return _analyzer_tab_label()


@callback(
    Output("analyzer-survey-select", "options"),
    Input(cn.L_ACTIVE_TAB_STORE, "data"),
)
def refresh_analyzer_list(tabs_value):
    """Refresh the survey dropdown when switching tabs. No
    prevent_initial_call: see refresh_survey_list above -- it should
    already be populated the moment the page loads.
    """
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
    Output(cn.L_ANALYZER_TABLE_SECTION, "style"),
    Input("analyzer-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def analyze_survey(survey_id):
    """Analyze survey responses and generate charts. The raw-data table
    section is hidden until a survey is actually chosen -- see
    survey_analyzer.survey_analyzer_layout, where it starts hidden.
    """
    if not survey_id:
        return [], [], [], [], {"display": "none"}

    survey = load_survey(survey_id)
    if not survey:
        return html.P("Survey not found."), [], [], [], {"display": "none"}

    responses = load_responses(survey_id)
    response_count, charts = _response_count_and_charts(survey, responses)
    table_style = {"maxWidth": "1000px", "margin": "0 auto"}

    if not responses:
        return response_count, charts, [], [], table_style

    table_data = []

    # Build table data
    headers = ["Response ID", "Respondent ID", "Submitted At"] + [
        f"Q{i+1}: {q.text[:30]}{'...' if len(q.text) > 30 else ''}"
        for i, q in enumerate(survey.questions)
    ]
    for resp in responses:
        row = {
            "Response ID": resp.id,
            "Respondent ID": resp.respondent_id,
            "Submitted At": resp.submitted_at,
        }
        for q in survey.questions:
            answer = resp.answers.get(q.id, "")
            if isinstance(answer, list):
                answer = ", ".join(str(a) for a in answer)
            col_name = f"Q{survey.questions.index(q)+1}: {q.text[:30]}"
            row[col_name] = str(answer)
        table_data.append(row)

    return response_count, charts, table_data, [{"name": h, "id": h} for h in headers], table_style


@callback(
    Output("analyzer-response-count", cn.L_CHILDREN, allow_duplicate=True),
    Output("analyzer-charts", cn.L_CHILDREN, allow_duplicate=True),
    Output(cn.L_ANALYZER_TAB_TOOLTIP, cn.L_CHILDREN, allow_duplicate=True),
    Input("analyzer-data-table", "data"),
    State("analyzer-data-table", "data_previous"),
    State("analyzer-survey-select", cn.L_VALUE),
    prevent_initial_call=True,
)
def delete_response_row(data, data_previous, survey_id):
    """Persist a row removed via the raw-data table's built-in delete ("x")
    control as an actual deletion, and refresh the dependent summary/charts
    (and the Analyzer tab's own hover, directly, rather than waiting for a
    tab switch).

    Guarded to fire only for a genuine single-row deletion -- exactly one
    fewer row, and every remaining id already present before -- rather than
    every "data" change: selecting a different survey also rewrites "data"
    (via analyze_survey), and without this guard would be misread as
    deleting every response that belonged to the previously-shown survey.
    """
    if not survey_id or not data_previous or len(data) != len(data_previous) - 1:
        return no_update, no_update, no_update

    previous_ids = {row["Response ID"] for row in data_previous}
    current_ids = {row["Response ID"] for row in data}
    removed_ids = previous_ids - current_ids
    if len(removed_ids) != 1 or not current_ids <= previous_ids:
        return no_update, no_update, no_update

    delete_response(next(iter(removed_ids)), survey_id)

    survey = load_survey(survey_id)
    if not survey:
        return no_update, no_update, no_update

    response_count, charts = _response_count_and_charts(survey, load_responses(survey_id))
    return response_count, charts, _analyzer_tab_label()

def has_duplicate_respondent_id(survey_id: str, respondent_id: str) -> bool:
    """Whether another response to this survey already used respondent_id."""
    responses = load_responses(survey_id)
    #result = any(r.id == respondent_id for r in responses)
    result = any(r.respondent_id == respondent_id for r in responses)
    return result


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
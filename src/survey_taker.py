"""SurveyTaker component - Fill out surveys as a participant."""

from dash import dcc, html

import constants as cn  # type: ignore
from form_logic import answer_value_for_qid  # type: ignore


def render_survey_taker(survey, initial_answers=None, status_message=None):
    """Render the form for taking a survey.

    `initial_answers` (a Draft's saved answers dict, keyed the same way as
    Response.answers) prefills every input when resuming a saved draft;
    omit it to render a blank form.

    `status_message` seeds the form's own "taker-status" div. A caller
    that rebuilds this whole form can't *also* target that nested div with
    a separate Output in the same callback response -- Dash applies a
    callback's Outputs in declaration order, so a later whole-form rebuild
    would just overwrite an earlier status update with the status div's
    own (empty) default. Passing the message in here instead avoids that.
    """
    question_components = []

    for q in survey.questions:
        qid = q.id
        label = f"Q{survey.questions.index(q) + 1}. {q.text}"
        if q.required:
            label += " *"

        input_component = _render_question_input(q, qid, initial_answers)

        question_components.append(html.Div([
            html.Label(label, style={
                "fontWeight": "bold",
                "marginTop": "15px",
                "display": "block",
            }),
            input_component,
        ]))

    return html.Div([
        html.H2(survey.title, style={"textAlign": "center"}),
        html.P(survey.description, style={"textAlign": "center", "fontSize": "16px", "color": "#666"}),
        html.Hr(),
        html.Div(question_components, style={"maxWidth": "700px", "margin": "0 auto"}),
        html.Div([
            html.Button(
                "Submit Survey",
                id="taker-submit",
                n_clicks=0,
                style={
                    "padding": "12px 30px",
                    "backgroundColor": "#4CAF50",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "display": "block",
                    "margin": "20px auto",
                },
            ),
        ], style={"textAlign": "center"}),
        html.Div(status_message, id="taker-status", style={
            "textAlign": "center",
            "marginTop": "15px",
            "fontWeight": "bold",
        }),
    ])


def _answer_id(qid):
    return {"type": "answer", "qid": qid}


def _render_question_input(question, qid, initial_answers=None):
    """Render the appropriate input component based on question type.

    Every answer input (including one per matrix row) uses the
    pattern-matching id {"type": "answer", "qid": ...} so a single,
    statically-registered submit callback can collect all answers for any
    survey via an ALL-pattern State. A matrix row's qid is the composite
    "{question_id}::{row_label}".

    `initial_answers` (a Draft's saved answers dict) prefills the input
    when resuming a saved draft; omit it to render blank/default values.
    """
    initial_answers = initial_answers or {}

    if question.type == "yesno":
        return html.Div([
            dcc.RadioItems(
                id=_answer_id(qid),
                options=[
                    {"label": "Yes", "value": "Yes"},
                    {"label": "No", "value": "No"},
                ],
                value=answer_value_for_qid(initial_answers, qid),
                inline=True,
            ),
        ])

    elif question.type == "checkbox" or question.type == "multiselect":
        return html.Div([
            dcc.Checklist(
                id=_answer_id(qid),
                options=[{"label": opt, "value": opt} for opt in question.options],
                value=answer_value_for_qid(initial_answers, qid) or [],
                inline=True,
            ),
        ])

    elif question.type == "likert":
        min_val = question.scale_min
        max_val = question.scale_max
        labels = []
        for v in range(min_val, max_val + 1):
            label = str(v)
            if v == min_val and question.scale_label_min:
                label = question.scale_label_min
            elif v == max_val and question.scale_label_max:
                label = question.scale_label_max
            labels.append({"label": label, "value": v})

        return html.Div([
            dcc.RadioItems(
                id=_answer_id(qid),
                options=labels,
                value=answer_value_for_qid(initial_answers, qid),
                inline=True,
            ),
        ])

    elif question.type == "numeric_scale":
        min_val = question.scale_min
        max_val = question.scale_max
        saved_value = answer_value_for_qid(initial_answers, qid)
        return html.Div([
            dcc.Slider(
                id=_answer_id(qid),
                min=min_val,
                max=max_val,
                step=1,
                value=saved_value if saved_value is not None else (min_val + max_val) // 2,
                marks={v: str(v) for v in range(min_val, max_val + 1)},
            ),
        ])

    elif question.type == "ranking":
        return html.Div([
            dcc.Dropdown(
                id=_answer_id(qid),
                options=[{"label": opt, "value": opt} for opt in question.options],
                multi=True,
                value=answer_value_for_qid(initial_answers, qid) or [],
                placeholder="Select and order items...",
            ),
        ])

    elif question.type == "matrix":
        # One radio-group per row (its answer is which column was picked).
        header_cells = [html.Th("")] + [html.Th(col) for col in question.matrix_cols]
        rows = []
        for row_label in question.matrix_rows:
            row_qid = f"{qid}::{row_label}"
            rows.append(html.Tr([
                html.Td(row_label),
                html.Td(
                    dcc.RadioItems(
                        id=_answer_id(row_qid),
                        options=[{"label": c, "value": c} for c in question.matrix_cols],
                        value=answer_value_for_qid(initial_answers, row_qid),
                        inline=True,
                    ),
                    colSpan=len(question.matrix_cols) or 1,
                ),
            ]))

        return html.Div([
            html.Table([
                html.Thead(html.Tr(header_cells)),
                html.Tbody(rows),
            ], style={"width": "100%", "borderCollapse": "collapse"})
        ])

    else:  # text
        return dcc.Textarea(
            id=_answer_id(qid),
            rows=3,
            value=answer_value_for_qid(initial_answers, qid) or "",
            placeholder="Type your answer here...",
            style={"width": "100%"},
        )


def survey_taker_layout():
    """Return the SurveyTaker page layout."""
    return html.Div([
        html.H2("Survey Taker", style={"textAlign": "center"}),

        # Survey selection
        html.Div([
            html.Label("Select a survey to take:"),
            dcc.Dropdown(
                id="taker-survey-select",
                options=[],
                value=None,
                clearable=True,
                placeholder="Choose a survey...",
                style={"marginBottom": "15px"},
            ),
            html.Div([
                html.Label("Resume a saved draft:"),
                dcc.Dropdown(
                    id=cn.L_TAKER_DRAFT_SELECT,
                    options=[],
                    value=None,
                    clearable=True,
                    placeholder="Start fresh, or resume a saved draft...",
                ),
            ], id=cn.L_TAKER_DRAFT_SECTION, style={"display": "none"}),
        ], style={"maxWidth": "600px", "margin": "0 auto 20px auto"}),

        # Survey form (shown when a survey is selected)
        html.Div(id="taker-survey-form"),

        # Save-for-later controls
        html.Div([
            dcc.Input(
                id=cn.L_TAKER_DRAFT_LABEL,
                type="text",
                value="",
                placeholder="Label this draft (optional)",
                style={"marginRight": "10px"},
            ),
            html.Button("Save for Later", id=cn.L_TAKER_SAVE_DRAFT, n_clicks=0),
            html.Button(
                "Delete This Draft",
                id=cn.L_TAKER_DELETE_DRAFT,
                n_clicks=0,
                style={"marginLeft": "10px"},
            ),
        ], style={"textAlign": "center", "marginTop": "10px"}),

        dcc.Store(id=cn.L_TAKER_CURRENT_DRAFT_STORE, data=None),

        # Thank you message
        html.Div(id="taker-thankyou", style={"display": "none"}),
    ], style={"padding": "20px"})
"""SurveyMaker component - Build surveys by defining questions and answer types."""
from __future__ import annotations

import json
from dash import dcc, html  # type: ignore
from dash import Input, Output, callback, no_update  # type: ignore

from models import Question, generate_id


QUESTION_TYPE_LABELS = {
    "checkbox": "Checkboxes (select all that apply)",
    "likert": "Likert Scale",
    "yesno": "Yes / No",
    "numeric_scale": "Numeric Scale (e.g., NPS 0-10)",
    "text": "Open-ended Text",
    "ranking": "Ranking",
    "multiselect": "Multi-select Checkboxes",
    "matrix": "Matrix / Grid",
}

QUESTION_TYPE_VALUES = list(QUESTION_TYPE_LABELS.keys())


def render_question_editor(question: Question | None, index: int):  # type: ignore
    """Render the editor UI for a single question."""
    q = question or Question(id=generate_id("q_"), type="text", text="", required=True)

    field_prefix = f"q_{index}_"

    # Options editor — pre-rendered placeholder so JS can populate it when type changes dynamically.
    # Uses a non-breaking space child to ensure Dash renders this div (React skips empty children).
    options_editor = html.Div(["\u00a0"], id=f"{field_prefix}options_list", style={"marginLeft": "20px", "marginTop": "5px"})

    # Matrix editor — placeholder for matrix type questions.
    matrix_editor = html.Div(["\u00a0"], id=f"{field_prefix}matrix_editor_div")

    # Scale editor — placeholder for likert/numeric_scale types.
    scale_editor = html.Div(["\u00a0"], id=f"{field_prefix}scale_editor_div", style={"marginLeft": "20px"})

    # Populate options editor for checkbox/multiselect/ranking types (initial render from stored data)
    if q.type in ("checkbox", "multiselect", "ranking"):
        option_inputs = []
        for i, opt in enumerate(q.options):
            option_inputs.append(html.Div([
                dcc.Input(
                    id=f"{field_prefix}opt_{i}",
                    value=opt,
                    type="text",
                    placeholder=f"Option {i+1}",
                    style={"width": "70%", "marginRight": "5px"},
                ),
                html.Button("\u2715", id=f"{field_prefix}del_opt_{i}", n_clicks=0),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}))

        # Reassign options_editor with populated content (placeholder div replaced)
        options_editor = html.Div([
            *option_inputs,
            html.Button("+ Add Option", id=f"{field_prefix}add_opt", n_clicks=0),
        ], id=f"{field_prefix}options_list", style={"marginLeft": "20px", "marginTop": "5px"})

    # Matrix editor (for matrix questions)
    if q.type == "matrix":
        row_inputs = []
        for i, row in enumerate(q.matrix_rows):
            row_inputs.append(html.Div([
                dcc.Input(
                    id=f"{field_prefix}row_{i}",
                    value=row,
                    type="text",
                    placeholder=f"Row {i+1}",
                    style={"width": "40%", "marginRight": "5px"},
                ),
                html.Button("\u2715", id=f"{field_prefix}del_row_{i}", n_clicks=0),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}))

        col_inputs = []
        for i, col in enumerate(q.matrix_cols):
            col_inputs.append(html.Div([
                dcc.Input(
                    id=f"{field_prefix}col_{i}",
                    value=col,
                    type="text",
                    placeholder=f"Column {i+1}",
                    style={"width": "40%", "marginRight": "5px"},
                ),
                html.Button("\u2715", id=f"{field_prefix}del_col_{i}", n_clicks=0),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}))

        matrix_editor = html.Div([
            html.P("Rows:", style={"fontWeight": "bold", "marginTop": "8px"}),
            html.Div(row_inputs, id=f"{field_prefix}rows_list"),
            html.Button("+ Add Row", id=f"{field_prefix}add_row", n_clicks=0),
            html.P("Columns:", style={"fontWeight": "bold", "marginTop": "8px"}),
            html.Div(col_inputs, id=f"{field_prefix}cols_list"),
            html.Button("+ Add Column", id=f"{field_prefix}add_col", n_clicks=0),
        ], style={"marginLeft": "20px", "marginTop": "5px"})

    # Scale editor (for likert and numeric_scale)
    if q.type in ("likert", "numeric_scale"):
        scale_editor = html.Div([
            html.Label("Scale Min:", style={"marginRight": "10px"}),
            dcc.Input(id=f"{field_prefix}scale_min", value=str(q.scale_min), type="number", style={"width": "60px", "marginRight": "10px"}),
            html.Label("Scale Max:", style={"marginRight": "10px"}),
            dcc.Input(id=f"{field_prefix}scale_max", value=str(q.scale_max), type="number", style={"width": "60px", "marginRight": "10px"}),
            html.Label("Min Label:", style={"marginRight": "10px"}),
            dcc.Input(id=f"{field_prefix}scale_label_min", value=q.scale_label_min, type="text", placeholder='e.g., \u201cStrongly Disagree\u201d', style={"width": "150px"}),
            html.Label("Max Label:", style={"marginRight": "10px"}),
            dcc.Input(id=f"{field_prefix}scale_label_max", value=q.scale_label_max, type="text", placeholder='e.g., \u201cStrongly Agree\u201d', style={"width": "150px"}),
        ], id=f"{field_prefix}scale_editor_div", style={"marginLeft": "20px", "marginTop": "5px"})

    return html.Div([
        html.H4(f"Question {index + 1}", style={"marginBottom": "5px"}),
        html.Div([
            html.Label("Question Type:"),
            dcc.Dropdown(
                id=f"{field_prefix}type",
                options=[{"label": v, "value": k} for k, v in QUESTION_TYPE_LABELS.items()],
                value=q.type,
                clearable=False,
            ),
        ], style={"marginBottom": "8px"}),

        html.Div([
            html.Label("Question Text:"),
            dcc.Textarea(
                id=f"{field_prefix}text",
                value=q.text,
                rows=2,
                style={"width": "100%"},
            ),
        ], style={"marginBottom": "8px"}),

        html.Div([
            dcc.Checklist(
                id=f"{field_prefix}required-check",
                options=[{"label": " Required ", "value": "req"}],
                value=["req"] if q.required else [],
            ),
        ], style={"marginBottom": "8px"}),

        # Type-dependent editors — placeholder divs always rendered so JS can populate them dynamically.
        options_editor,
        scale_editor,
        matrix_editor,
        html.Button(
            "\U0001f5d1\ufe0f Delete Question",
            id=f"delete_q_{index}",
            n_clicks=0,
            style={"marginTop": "10px"},
        ),
        html.Hr(style={"marginTop": "15px", "marginBottom": "15px"}),
    ], style={
        "border": "1px solid #ddd",
        "borderRadius": "8px",
        "padding": "15px",
        "backgroundColor": "#fafafa",
        "marginBottom": "15px",
    })
def survey_maker_layout():
    """Return the SurveyMaker page layout."""
    return html.Div([
        html.H2("Survey Maker", style={"textAlign": "center"}),

        # Existing surveys dropdown
        html.Div([
            html.Label("Select an existing survey to edit:"),
            dcc.Dropdown(
                id="maker-survey-select",
                options=[],
                value=None,
                clearable=True,
                placeholder="Choose a survey...",
                style={"marginBottom": "15px"},
            ),
        ], style={"maxWidth": "600px", "margin": "0 auto 20px auto"}),

        # Survey metadata
        html.Div([
            html.Label("Survey Title:"),
            dcc.Input(
                id="maker-title",
                type="text",
                placeholder="Enter survey title...",
                style={"width": "100%", "padding": "8px", "marginBottom": "10px"},
            ),
            html.Label("Description:"),
            dcc.Textarea(
                id="maker-description",
                value="",
                rows=3,
                placeholder="Enter survey description...",
                style={"width": "100%", "padding": "8px", "marginBottom": "15px"},
            ),
        ], style={"maxWidth": "600px", "margin": "0 auto 20px auto"}),

        # Questions container — populated by make_question_components() callbacks
        html.Div(id="maker-questions-container"),

        # Action buttons
        html.Div([
            html.Button(
                "+ Add Question",
                id="maker-add-question",
                n_clicks=0,
                style={
                    "padding": "10px 20px",
                    "backgroundColor": "#4CAF50",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "marginRight": "10px",
                },
            ),
            html.Button(
                "\U0001f4be Save Survey",
                id="maker-save-survey",
                n_clicks=0,
                style={
                    "padding": "10px 20px",
                    "backgroundColor": "#2196F3",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "marginRight": "10px",
                },
            ),
        ], style={"textAlign": "center", "marginTop": "20px"}),

        # Status message
        html.Div(id="maker-status", style={
            "textAlign": "center",
            "marginTop": "15px",
            "fontWeight": "bold",
            "color": "#4CAF50",
        }),

        dcc.Store(id="maker-questions-store"),
    ], style={"padding": "20px", "maxWidth": "900px", "margin": "0 auto"})

def make_question_components(n_questions: int):
    """Generate question editor components for n questions."""
    editors = []
    for i in range(n_questions):
        editors.append(render_question_editor(None, i))
    return editors


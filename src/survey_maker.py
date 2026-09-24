"""SurveyMaker component - Build surveys by defining questions and answer types."""
from __future__ import annotations

import constants as cn

from dash import dcc, html  # type: ignore

from models import Question, generate_id
from form_logic import list_to_lines, type_visibility, section_style


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


def render_question_editor(question: Question | None, qid: str):  # type: ignore
    """Render the editor UI for a single question, keyed by its stable `qid`.

    Every field uses a pattern-matching id of the form {"type": <field>, "qid": qid}
    so callbacks can address one question's fields (MATCH) or every question's
    fields at once (ALL) without depending on the question's position in the list.

    All type-specific sections (options / scale / matrix) are always rendered;
    only their visibility changes with the selected type, so switching a
    question's type never destroys already-entered data in other sections.
    """
    q = question or Question(id=qid, type="text", text="", required=True)  # type: ignore

    visibility = type_visibility(q.type)

    def fid(field: str) -> dict:
        return {"type": field, "qid": qid}

    options_editor = html.Div([
        html.Label("Options (one per line):"),
        dcc.Textarea(
            id=fid("q-options"),
            value=list_to_lines(q.options),
            rows=4,
            placeholder="Option 1\nOption 2\nOption 3",
            style={"width": "100%"},
        ),
    ], id=fid("q-options-wrap"), style=section_style(visibility["options"]))

    scale_editor = html.Div([
        html.Label("Scale Min:", style={"marginRight": "10px"}),
        dcc.Input(id=fid("q-scale-min"), value=str(q.scale_min), type="number", style={"width": "60px", "marginRight": "10px"}),
        html.Label("Scale Max:", style={"marginRight": "10px"}),
        dcc.Input(id=fid("q-scale-max"), value=str(q.scale_max), type="number", style={"width": "60px", "marginRight": "10px"}),
        html.Label("Min Label:", style={"marginRight": "10px"}),
        dcc.Input(id=fid("q-scale-label-min"), value=q.scale_label_min, type="text", placeholder='e.g., “Strongly Disagree”', style={"width": "150px"}),
        html.Label("Max Label:", style={"marginRight": "10px"}),
        dcc.Input(id=fid("q-scale-label-max"), value=q.scale_label_max, type="text", placeholder='e.g., “Strongly Agree”', style={"width": "150px"}),
    ], id=fid("q-scale-wrap"), style=section_style(visibility["scale"]))

    matrix_editor = html.Div([
        html.Label("Rows (one per line):"),
        dcc.Textarea(
            id=fid("q-matrix-rows"),
            value=list_to_lines(q.matrix_rows),
            rows=3,
            placeholder="Row 1\nRow 2",
            style={"width": "100%"},
        ),
        html.Label("Columns (one per line):"),
        dcc.Textarea(
            id=fid("q-matrix-cols"),
            value=list_to_lines(q.matrix_cols),
            rows=3,
            placeholder="Column 1\nColumn 2",
            style={"width": "100%"},
        ),
    ], id=fid("q-matrix-wrap"), style=section_style(visibility["matrix"]))

    return html.Div([
        html.Div([
            html.Label("Question Type:"),
            dcc.Dropdown(
                id=fid("q-type"),
                options=[{"label": v, "value": k} for k, v in QUESTION_TYPE_LABELS.items()],
                value=q.type,
                clearable=False,
            ),
        ], style={"marginBottom": "8px"}),

        html.Div([
            html.Label("Question Text:"),
            dcc.Textarea(
                id=fid("q-text"),
                value=q.text,
                rows=2,
                style={"width": "100%"},
            ),
        ], style={"marginBottom": "8px"}),

        html.Div([
            dcc.Checklist(
                id=fid("q-required"),
                options=[{"label": " Required ", "value": "req"}],
                value=["req"] if q.required else [],
            ),
        ], style={"marginBottom": "8px"}),

        options_editor,
        scale_editor,
        matrix_editor,
        html.Button(
            "\U0001f5d1️ Delete Question",
            id=fid("delete-q"),
            n_clicks=0,
            style={"marginTop": "10px"},
        ),
        html.Hr(style={"marginTop": "15px", "marginBottom": "15px"}),
    ], id=fid("q-wrapper"), style={
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

        # Existing surveys dropdown + Create New Survey button
        html.Div([
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
            ], style={
                "maxWidth": "420px",
                "display": "inline-block",
                "verticalAlign": "top",
            }),
            html.Div([
                html.Button(
                    "\U0001f4dd Create New Survey",
                    id="maker-create-new",
                    n_clicks=0,
                    style={
                        "padding": "10px 20px",
                        "backgroundColor": "#ff9800",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "cursor": "pointer",
                        "fontSize": "16px",
                        "display": "block",
                        "marginBottom": "10px",
                    },
                ),
                html.Button(
                    "\U0001f5d1️ Delete Survey",
                    id="maker-delete-survey",
                    n_clicks=0,
                    style={
                        "padding": "10px 20px",
                        "backgroundColor": "#e53935",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "cursor": "pointer",
                        "fontSize": "16px",
                        "display": "block",
                    },
                ),
            ], style={
                "maxWidth": "200px",
                "display": "inline-block",
                "verticalAlign": "top",
                "marginLeft": "20px",
            }),
        ], style={
            "maxWidth": "640px",
            "margin": "0 auto 20px auto",
        }),

        dcc.ConfirmDialog(
            id="maker-delete-confirm",
            message="",
        ),

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

        # Questions container — populated by the load/add/delete question callbacks
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
                id=cn.L_MAKER_SAVE_SURVEY,
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
    ], style={"padding": "20px", "maxWidth": "900px", "margin": "0 auto"})

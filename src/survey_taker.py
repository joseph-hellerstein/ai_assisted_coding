"""SurveyTaker component - Fill out surveys as a participant."""

from dash import dcc, html


def render_survey_taker(survey):
    """Render the form for taking a survey."""
    question_components = []

    for q in survey.questions:
        qid = q.id
        label = f"Q{survey.questions.index(q) + 1}. {q.text}"
        if q.required:
            label += " *"

        input_component = _render_question_input(q, qid)

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
        html.Div(id="taker-status", style={
            "textAlign": "center",
            "marginTop": "15px",
            "fontWeight": "bold",
        }),
    ])


def _render_question_input(question, qid):
    """Render the appropriate input component based on question type."""
    prefix = f"answer_{qid}_"

    if question.type == "yesno":
        return html.Div([
            dcc.RadioItems(
                id=prefix + "value",
                options=[
                    {"label": "Yes", "value": "Yes"},
                    {"label": "No", "value": "No"},
                ],
                inline=True,
            ),
        ])

    elif question.type == "checkbox" or question.type == "multiselect":
        return html.Div([
            dcc.Checklist(
                id=prefix + "value",
                options=[{"label": opt, "value": opt} for opt in question.options],
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
                id=prefix + "value",
                options=labels,
                inline=True,
            ),
        ])

    elif question.type == "numeric_scale":
        min_val = question.scale_min
        max_val = question.scale_max
        return html.Div([
            dcc.Slider(
                id=prefix + "value",
                min=min_val,
                max=max_val,
                step=1,
                value=(min_val + max_val) // 2,
                marks={v: str(v) for v in range(min_val, max_val + 1)},
            ),
        ])

    elif question.type == "ranking":
        return html.Div([
            dcc.Dropdown(
                id=prefix + "value",
                options=[{"label": opt, "value": opt} for opt in question.options],
                multi=True,
                placeholder="Select and order items...",
            ),
        ])

    elif question.type == "matrix":
        # Render a table-like matrix
        header_cells = [html.Th("")] + [html.Th(col) for col in question.matrix_cols]
        rows = []
        for row_label in question.matrix_rows:
            cells = [html.Td(row_label)]
            for _ in question.matrix_cols:
                cells.append(html.Td(
                    dcc.RadioItems(
                        id=f"{prefix}matrix_{row_label}",
                        options=[{"label": c, "value": c} for c in question.matrix_cols],
                        inline=True,
                    )
                ))
            rows.append(html.Tr(cells))

        return html.Div([
            html.Table([
                html.Thead(html.Tr(header_cells)),
                html.Tbody(rows),
            ], style={"width": "100%", "borderCollapse": "collapse"})
        ])

    else:  # text
        return dcc.Textarea(
            id=prefix + "value",
            rows=3,
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
        ], style={"maxWidth": "600px", "margin": "0 auto 20px auto"}),

        # Survey form (shown when a survey is selected)
        html.Div(id="taker-survey-form"),

        # Thank you message
        html.Div(id="taker-thankyou", style={"display": "none"}),
    ], style={"padding": "20px"})
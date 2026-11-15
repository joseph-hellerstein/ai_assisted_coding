"""Layout of the Survey Taker tab, and the form for one survey."""
from dash import dcc, html

import src.constants as cn
from src.models import Question, Survey


def taker_layout() -> html.Div:
    return html.Div([
        html.H3("Take a survey"),
        dcc.Dropdown(id=cn.TAKER_SURVEY_SELECT, placeholder="Choose a survey..."),
        html.Div(id=cn.TAKER_FORM, style={"marginTop": "16px"}),
    ], style={"maxWidth": "700px", "margin": "0 auto"})


def _answer_input(question: Question):
    answer_id = {"type": cn.ANSWER, "qid": question.id}
    if question.type == "yesno":
        return dcc.RadioItems(id=answer_id, options=["Yes", "No"], inline=True)
    if question.type == "checkbox":
        return dcc.Checklist(id=answer_id, options=question.options)
    return dcc.Textarea(id=answer_id, style={"width": "100%"})


def render_survey_form(survey: Survey) -> html.Div:
    questions = [
        html.Div([
            html.Label(f"Q{number}. {q.text}", style={"fontWeight": "bold", "display": "block"}),
            _answer_input(q),
        ], style={"marginTop": "14px"})
        for number, q in enumerate(survey.questions, start=1)
    ]
    return html.Div([
        html.H4(survey.title),
        html.P(survey.description),
        html.Label("Your ID (5 digits): "),
        dcc.Input(id=cn.TAKER_RESPONDENT_ID, type="text", maxLength=5, placeholder="5 digits"),
        html.Div(questions),
        html.Button("Submit", id=cn.TAKER_SUBMIT, n_clicks=0, style={"marginTop": "16px"}),
        html.Div(id=cn.TAKER_STATUS, style={"marginTop": "12px"}),
    ])

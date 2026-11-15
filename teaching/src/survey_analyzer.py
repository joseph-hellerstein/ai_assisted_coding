"""Layout of the Survey Analyzer tab, and the charts and table it shows."""
from __future__ import annotations

import re
from collections import Counter

import plotly.graph_objects as go
from dash import dash_table, dcc, html

import src.constants as cn
from src.models import Question, Response, Survey

# A word is letters or digits, optionally joined by apostrophes ("don't"); quotes around it are dropped.
WORD = r"[^\W_]+(?:'[^\W_]+)*"


def analyzer_layout() -> html.Div:
    return html.Div([
        html.H3("Analyze a survey"),
        dcc.Dropdown(id=cn.ANALYZER_SURVEY_SELECT, placeholder="Choose a survey..."),
        html.Div(id=cn.ANALYZER_RESULTS, style={"marginTop": "16px"}),
    ], style={"maxWidth": "900px", "margin": "0 auto"})


def word_counts(texts: list[str], top_n: int = 15) -> list[tuple[str, int]]:
    """The most common words in some text answers, ignoring case and punctuation."""
    counts = Counter(word for text in texts for word in re.findall(WORD, text.lower()))
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]


def question_chart(question: Question, responses: list[Response]) -> go.Figure:
    """A bar chart summarizing every response's answer to one question."""
    answers = [r.answers[question.id] for r in responses if question.id in r.answers]
    if question.type == "yesno":
        labels = ["Yes", "No"]
        counts = [answers.count(label) for label in labels]
    elif question.type == "checkbox":
        labels = question.options
        counts = [sum(option in answer for answer in answers) for option in labels]
    else:  # text
        pairs = word_counts([a for a in answers if isinstance(a, str)])
        labels = [word for word, _ in pairs]
        counts = [count for _, count in pairs]
    fig = go.Figure(go.Bar(x=labels, y=counts))
    fig.update_layout(title=question.text, height=300, margin={"t": 50, "b": 40})
    return fig


def response_table(survey: Survey, responses: list[Response]) -> dash_table.DataTable:
    """One row per response, one column per question."""
    columns = [{"name": "Respondent ID", "id": "respondent_id"}, {"name": "Submitted", "id": "submitted_at"}]
    columns += [{"name": q.text, "id": q.id} for q in survey.questions]
    rows = []
    for r in responses:
        row = {"respondent_id": r.respondent_id, "submitted_at": r.submitted_at}
        for q in survey.questions:
            answer = r.answers.get(q.id, "")
            row[q.id] = ", ".join(answer) if isinstance(answer, list) else answer
        rows.append(row)
    return dash_table.DataTable(columns=columns, data=rows, style_cell={"textAlign": "left"})


def build_results(survey: Survey, responses: list[Response]) -> html.Div:
    """Everything the Analyzer shows for one survey."""
    count = html.H4(f"Responses: {len(responses)}")
    if not responses:
        return html.Div([count, html.P("No responses yet")])
    charts = [dcc.Graph(figure=question_chart(q, responses)) for q in survey.questions]
    return html.Div([count, *charts, response_table(survey, responses)])

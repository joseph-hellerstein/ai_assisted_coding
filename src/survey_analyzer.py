"""SurveyAnalyzer component - Generate reports on survey results."""
from __future__ import annotations


from dash import dcc, html  # type: ignore
from dash import dash_table  # type: ignore
import plotly.graph_objects as go  # type: ignore
import pandas as pd  # type: ignore
from collections import Counter  # type: ignore

from storage import list_surveys, load_survey, load_responses


def survey_analyzer_layout():
    """Return the SurveyAnalyzer page layout."""
    return html.Div([
        html.H2("Survey Analyzer", style={"textAlign": "center"}),

        # Survey selection
        html.Div([
            html.Label("Select a survey to analyze:"),
            dcc.Dropdown(
                id="analyzer-survey-select",
                options=[],
                value=None,
                clearable=True,
                placeholder="Choose a survey...",
                style={"marginBottom": "15px"},
            ),
        ], style={"maxWidth": "600px", "margin": "0 auto 20px auto"}),

        # Response count summary
        html.Div(id="analyzer-response-count"),

        # Charts container
        html.Div(id="analyzer-charts"),

        # Raw data table
        html.Div([
            html.H3("Raw Responses", style={"marginTop": "30px"}),
            dash_table.DataTable(
                id="analyzer-data-table",
                page_size=15,
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "minWidth": "100px",
                },
                style_header={
                    "backgroundColor": "#f5f5f5",
                    "fontWeight": "bold",
                },
            ),
        ], style={"maxWidth": "1000px", "margin": "0 auto"}),

        dcc.Store(id="analyzer-responses-store"),
    ], style={"padding": "20px"})


# Note: The analyze_survey callback is defined in app.py to avoid
# duplicate callback registration when both files are imported.


def _generate_question_chart(question, responses):
    """Generate a Plotly chart for a single question's responses."""
    answers = [r.answers.get(question.id) for r in responses]

    if question.type == "yesno":
        counts = Counter(str(a) for a in answers if a is not None)
        return _bar_chart(counts, f"Responses to: {question.text}")

    elif question.type in ("checkbox", "multiselect"):
        # Count individual option selections
        all_options = question.options
        opt_counts = Counter()
        for a in answers:
            if isinstance(a, list):
                for item in a:
                    opt_counts[item] += 1
        return _bar_chart(opt_counts, f"Selections for: {question.text}")

    elif question.type == "likert":
        counts = Counter(str(a) for a in answers if a is not None)
        min_val = question.scale_min
        max_val = question.scale_max
        # Ensure all values are represented
        for v in range(min_val, max_val + 1):
            if str(v) not in counts:
                counts[str(v)] = 0
        return _bar_chart(counts, f"Responses to: {question.text}",
                         x_order=list(range(min_val, max_val + 1)))

    elif question.type == "numeric_scale":
        numeric_answers = [a for a in answers if isinstance(a, (int, float))]
        if not numeric_answers:
            return None
        return _histogram(numeric_answers, f"Responses to: {question.text}",
                         bin_range=(question.scale_min, question.scale_max + 1))

    elif question.type == "ranking":
        # Count how often each option appears (regardless of position)
        opt_counts = Counter()
        for a in answers:
            if isinstance(a, list):
                opt_counts.update(a)
        return _bar_chart(opt_counts, f"Selections for: {question.text}")

    elif question.type == "matrix":
        # Generate one chart per matrix row
        charts = []
        for row_label in question.matrix_rows:
            row_answers = [r.answers.get(f"{question.id}_matrix_{row_label}") for r in responses]
            counts = Counter(str(a) for a in row_answers if a is not None)
            fig = _bar_chart(counts, f"{row_label}",
                            x_order=question.matrix_cols)
            charts.append(fig)
        # Return combined figure with subplots
        if len(charts) == 1:
            return charts[0]
        return None  # Complex to combine; skip for now

    else:  # text - no chart, just word frequency
        text_answers = [a for a in answers if isinstance(a, str) and len(a.strip()) > 0]
        if not text_answers:
            return None
        # Simple word frequency
        all_words = []
        for text in text_answers:
            words = text.lower().split()
            all_words.extend(words[:20])  # Limit to first 20 words per answer
        word_counts = Counter(all_words).most_common(15)
        if not word_counts:
            return None
        labels, values = zip(*word_counts)
        fig = go.Figure(data=[go.Bar(x=list(labels), y=list(values))])
        fig.update_layout(
            title=f"Word frequency: {question.text}",
            xaxis_title="Word",
            yaxis_title="Count",
            height=400,
        )
        return fig


def _bar_chart(counts: Counter, title: str, x_order: list | None = None):
    """Create a bar chart from a Counter."""
    if not counts:
        return go.Figure().add_annotation(text="No responses", showarrow=False)

    labels = list(counts.keys())
    values = list(counts.values())

    if x_order:
        # Reorder to match specified order
        ordered_counts = {k: 0 for k in x_order}
        for k, v in counts.items():
            if k in ordered_counts:
                ordered_counts[k] = v
        labels = list(ordered_counts.keys())
        values = list(ordered_counts.values())

    fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color="#2196F3")])
    fig.update_layout(
        title=title,
        xaxis_title="Response",
        yaxis_title="Count",
        height=400,
    )
    return fig


def _histogram(values: list, title: str, bin_range: tuple | None = None):
    """Create a histogram from numeric values."""
    if not values:
        return go.Figure().add_annotation(text="No responses", showarrow=False)

    fig = go.Figure(data=[go.Histogram(x=values, marker_color="#4CAF50")])
    if bin_range:
        fig.update_xaxes(range=bin_range)
    fig.update_layout(
        title=title,
        xaxis_title="Value",
        yaxis_title="Count",
        height=400,
    )
    return fig
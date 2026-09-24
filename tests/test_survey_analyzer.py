"""Tests for chart generation in src/survey_analyzer.py."""

from models import Question, Response
from survey_analyzer import _generate_question_chart


def _bar_values_by_label(fig):
    """Map each bar's x label (stringified) to its y value."""
    trace = fig.data[0]
    return {str(x): y for x, y in zip(trace.x, trace.y)}


def test_likert_chart_reflects_the_actual_response_counts():
    # Regression test: a Likert question's answers are stored as ints
    # (e.g. 4), but the chart's x_order was a list of ints while the
    # counts dict used string keys, so real answers never matched their
    # x_order slot and every bar rendered as 0 regardless of the actual
    # data underneath.
    q = Question(id="q_1", type="likert", text="How much do you like summer?",
                 scale_min=1, scale_max=5)
    responses = [
        Response(id="r1", survey_id="s1", submitted_at="", answers={"q_1": 4}),
    ]

    fig = _generate_question_chart(q, responses)

    values = _bar_values_by_label(fig)
    assert values["4"] == 1, f"expected the one response of 4 to show up, got {values}"


def test_likert_chart_counts_multiple_responses_at_different_values():
    q = Question(id="q_1", type="likert", text="Rate it", scale_min=1, scale_max=5)
    responses = [
        Response(id="r1", survey_id="s1", submitted_at="", answers={"q_1": 2}),
        Response(id="r2", survey_id="s1", submitted_at="", answers={"q_1": 2}),
        Response(id="r3", survey_id="s1", submitted_at="", answers={"q_1": 5}),
    ]

    fig = _generate_question_chart(q, responses)

    values = _bar_values_by_label(fig)
    assert values["2"] == 2
    assert values["5"] == 1
    assert values["1"] == 0
    assert values["3"] == 0
    assert values["4"] == 0

"""Tests for chart generation in src/survey_analyzer.py."""

from models import Question, Response # type: ignore
from survey_analyzer import _generate_question_chart, survey_analyzer_layout  # type: ignore


def _collect_by_id(component, out=None):
    if out is None:
        out = {}
    cid = getattr(component, "id", None)
    if cid is not None:
        out[cid] = component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for c in children:
            _collect_by_id(c, out)
    elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
        _collect_by_id(children, out)
    return out


def test_survey_analyzer_layout_hides_the_raw_responses_table_until_a_survey_is_chosen():
    # The "Raw Responses" table shouldn't appear until a survey is picked
    # (see analyze_survey in app.py, which reveals this section).
    layout = survey_analyzer_layout()
    ids = _collect_by_id(layout)
    assert "analyzer-table-section" in ids
    assert ids["analyzer-table-section"].style.get("display") == "none"


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

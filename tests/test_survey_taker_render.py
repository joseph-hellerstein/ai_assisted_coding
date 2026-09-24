"""Tests for Survey Taker answer-input rendering (src/survey_taker.py).

Answer inputs use a pattern-matching id {"type": "answer", "qid": ...} so a
single, statically-registered submit callback can collect every answer via
an ALL-pattern State, regardless of survey/question count. Matrix questions
render one input per row, keyed by the composite qid "{question_id}::{row}".
"""

from models import Question # type: ignore
from survey_taker import _render_question_input  # type: ignore


def _collect_ids(component, out=None):
    if out is None:
        out = []
    cid = getattr(component, "id", None)
    if cid is not None:
        out.append(cid)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for c in children:
            _collect_ids(c, out)
    elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
        _collect_ids(children, out)
    return out


def test_text_question_uses_answer_pattern_id_keyed_by_question_id():
    q = Question(id="q_1", type="text", text="Tell us more")
    component = _render_question_input(q, q.id)
    ids = _collect_ids(component)
    assert {"type": "answer", "qid": "q_1"} in ids


def test_yesno_question_uses_answer_pattern_id():
    q = Question(id="q_2", type="yesno", text="Would you recommend us?")
    component = _render_question_input(q, q.id)
    ids = _collect_ids(component)
    assert {"type": "answer", "qid": "q_2"} in ids


def test_checkbox_question_uses_answer_pattern_id():
    q = Question(id="q_3", type="checkbox", text="Pick some", options=["A", "B"])
    component = _render_question_input(q, q.id)
    ids = _collect_ids(component)
    assert {"type": "answer", "qid": "q_3"} in ids


def test_matrix_question_uses_one_composite_answer_id_per_row():
    q = Question(id="q_4", type="matrix", text="Rate these",
                 matrix_rows=["Speed", "Quality"], matrix_cols=["Poor", "Good"])
    component = _render_question_input(q, q.id)
    ids = _collect_ids(component)
    assert {"type": "answer", "qid": "q_4::Speed"} in ids
    assert {"type": "answer", "qid": "q_4::Quality"} in ids

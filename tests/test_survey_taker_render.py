"""Tests for Survey Taker answer-input rendering (src/survey_taker.py).

Answer inputs use a pattern-matching id {"type": "answer", "qid": ...} so a
single, statically-registered submit callback can collect every answer via
an ALL-pattern State, regardless of survey/question count. Matrix questions
render one input per row, keyed by the composite qid "{question_id}::{row}".
"""

from models import Question, Survey  # type: ignore
from survey_taker import _render_question_input, render_survey_taker, survey_taker_layout  # type: ignore

from typing import cast


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


def _find_by_id(component, target_id, out=None):
    cid = getattr(component, "id", None)
    if cid == target_id:
        return component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for c in children:
            found = _find_by_id(c, target_id)
            if found is not None:
                return found
    elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
        return _find_by_id(children, target_id)
    return None


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


def test_text_question_prefills_value_from_initial_answers():
    q = Question(id="q_1", type="text", text="Tell us more")
    component = _render_question_input(q, q.id, initial_answers={"q_1": "Already typed this"})
    assert component.value == "Already typed this"


def test_checkbox_question_prefills_selected_options_from_initial_answers():
    q = Question(id="q_3", type="checkbox", text="Pick some", options=["A", "B"])
    component = _render_question_input(q, q.id, initial_answers={"q_3": ["A"]})
    checklist = component.children[0]
    assert checklist.value == ["A"]


def test_checkbox_question_defaults_to_empty_list_with_no_initial_answer():
    q = Question(id="q_3", type="checkbox", text="Pick some", options=["A", "B"])
    component = _render_question_input(q, q.id)
    checklist = component.children[0]
    assert checklist.value == []


def test_render_survey_taker_prefills_matrix_row_from_initial_answers():
    q = Question(id="q_4", type="matrix", text="Rate these",
                 matrix_rows=["Speed", "Quality"], matrix_cols=["Poor", "Good"])
    survey = Survey(id="srv_1", title="T", questions=[q])

    form = render_survey_taker(survey, initial_answers={"q_4_matrix_Speed": "Good"})

    radio = _find_by_id(form, {"type": "answer", "qid": "q_4::Speed"})
    assert radio.value == "Good"


def test_render_survey_taker_embeds_a_status_message_into_its_own_status_div():
    # A caller that rebuilds the whole form in the same callback response as
    # a status update (e.g. after deleting a draft) can't also target the
    # nested "taker-status" div with a separate Output -- Dash applies
    # per-callback Outputs in declaration order, so a later whole-form
    # rebuild would just overwrite an earlier, separate status update with
    # the status div's own (empty) default. Baking the message into the
    # same render call sidesteps that entirely.
    survey = Survey(id="srv_1", title="T", questions=[])

    form = render_survey_taker(survey, status_message="Draft deleted.")

    status_div = _find_by_id(form, "taker-status")
    assert status_div.children == "Draft deleted."  # type: ignore


def test_render_survey_taker_prefills_a_random_five_digit_respondent_id_by_default():
    survey = Survey(id="srv_1", title="T", questions=[])

    form = render_survey_taker(survey)

    field = _find_by_id(form, "taker-respondent-id")
    assert field is not None
    assert len(field.value) == 5
    assert field.value.isdigit()


def test_render_survey_taker_uses_the_given_respondent_id_when_provided():
    survey = Survey(id="srv_1", title="T", questions=[])

    form = render_survey_taker(survey, initial_respondent_id="54321")

    field = _find_by_id(form, "taker-respondent-id")
    assert field.value == "54321" # type: ignore


def test_survey_taker_layout_has_a_take_another_survey_button_in_the_thank_you_screen():
    # The thank-you screen used to be a dead end (an empty div) -- there was
    # no way to take a second survey without switching tabs away and back.
    layout = survey_taker_layout()
    button = _find_by_id(layout, "taker-take-another")
    assert button is not None


def test_survey_taker_layout_hides_the_save_for_later_controls_until_a_survey_is_chosen():
    # The "Save for Later" / "Delete This Draft" controls shouldn't appear
    # until a survey is picked (see show_survey in app.py, which reveals
    # this section).
    layout = survey_taker_layout()
    controls = _find_by_id(layout, "taker-draft-controls")
    assert controls is not None
    assert controls.style.get("display") == "none"

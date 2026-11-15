import pytest
from dash import no_update

import src.constants as cn
from src.app import refresh_survey_lists, show_survey, submit_survey_response
from src.models import Question, Survey
from src.storage import load_responses, save_survey


@pytest.fixture
def survey(tmp_storage):
    s = Survey(id="srv_demo", title="Demo", questions=[
        Question(id="q_text", type="text", text="Comments?"),
        Question(id="q_yn", type="yesno", text="Attended?"),
        Question(id="q_cb", type="checkbox", text="Colors?", options=["Red", "Blue"]),
    ])
    save_survey(s)
    return s


def _answer_ids(survey):
    return [{"type": cn.ANSWER, "qid": q.id} for q in survey.questions]


def _components(tree):
    return list(tree._traverse()) + [tree]


def test_refresh_survey_lists_fills_both_dropdowns(survey):
    taker_options, analyzer_options = refresh_survey_lists("taker")
    assert taker_options == analyzer_options == [{"label": "Demo", "value": "srv_demo"}]


def test_show_survey_renders_one_answer_input_per_question(survey):
    components = _components(show_survey("srv_demo"))
    answer_ids = [c.id for c in components if isinstance(getattr(c, "id", None), dict)
                  and c.id.get("type") == cn.ANSWER]
    assert answer_ids == _answer_ids(survey)
    [id_field] = [c for c in components if getattr(c, "id", None) == cn.TAKER_RESPONDENT_ID]
    assert getattr(id_field, "value", None) in (None, "")
    assert any(getattr(c, "id", None) == cn.TAKER_SUBMIT for c in components)


def test_show_survey_with_no_selection_is_empty():
    assert show_survey(None) == []


def test_show_survey_for_missing_file_says_so(tmp_storage):
    assert "no longer exists" in str(show_survey("srv_gone"))


def test_submit_saves_response_and_disables_button(survey):
    status, disabled = submit_survey_response(
        1, "srv_demo", "12345", [None, "Yes", []], _answer_ids(survey))
    assert "Thank you" in str(status)
    assert disabled is True
    [response] = load_responses("srv_demo")
    assert response.answers == {"q_yn": "Yes"}
    assert response.respondent_id == "12345"


@pytest.mark.parametrize("respondent_id", ["12", "abcde", None])
def test_submit_rejects_bad_or_cleared_id_and_keeps_button(survey, respondent_id):
    status, disabled = submit_survey_response(
        1, "srv_demo", respondent_id, [None, "Yes", []], _answer_ids(survey))
    assert "Your ID must be exactly 5 digits." in str(status)
    assert disabled is no_update
    assert load_responses("srv_demo") == []


def test_submit_for_missing_survey_saves_nothing(tmp_storage):
    status, _ = submit_survey_response(1, "srv_gone", "12345", [], [])
    assert "no longer exists" in str(status)
    assert load_responses("srv_gone") == []

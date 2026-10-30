"""Tests for src/sample_data.py (the landing-page "Test" panel's backend).

These monkeypatch sample_data's own bound storage names, the same way
tests/test_app_callbacks.py monkeypatches app.py's, so no real storage is
touched.
"""
import random

import sample_data  # type: ignore
from models import Question, Survey  # type: ignore


def test_generate_random_survey_uses_the_recognizable_id_prefix():
    saved = {}
    sample_data.save_survey = lambda survey: saved.__setitem__("survey", survey)

    survey = sample_data.generate_random_survey(rng=random.Random(1))

    assert survey.id.startswith(sample_data.RANDOM_SURVEY_ID_PREFIX)
    assert saved["survey"] is survey


def test_generate_random_survey_has_a_plausible_number_of_questions():
    sample_data.save_survey = lambda survey: None

    survey = sample_data.generate_random_survey(rng=random.Random(2))

    assert 3 <= len(survey.questions) <= 8
    assert all(q.id.startswith(survey.id) for q in survey.questions)


def test_generate_random_survey_cycles_through_multiple_question_types():
    sample_data.save_survey = lambda survey: None

    survey = sample_data.generate_random_survey(rng=random.Random(3))

    assert len(set(q.type for q in survey.questions)) > 1


def test_generate_random_survey_title_starts_with_test():
    sample_data.save_survey = lambda survey: None
    sample_data.list_surveys = lambda: []

    survey = sample_data.generate_random_survey(rng=random.Random(6))

    assert survey.title.startswith("Test ")


def test_generate_random_survey_title_is_deduplicated_with_a_number():
    sample_data.save_survey = lambda survey: None
    original_topics = sample_data._TOPICS
    sample_data._TOPICS = ["Travel Plans"]
    try:
        sample_data.list_surveys = lambda: [
            {"id": "srv_rand_1", "title": "Test Travel Plans Survey"},
        ]
        survey = sample_data.generate_random_survey(rng=random.Random(7))
        assert survey.title == "Test Travel Plans Survey 2"

        sample_data.list_surveys = lambda: [
            {"id": "srv_rand_1", "title": "Test Travel Plans Survey"},
            {"id": "srv_rand_2", "title": "Test Travel Plans Survey 2"},
        ]
        survey = sample_data.generate_random_survey(rng=random.Random(8))
        assert survey.title == "Test Travel Plans Survey 3"
    finally:
        sample_data._TOPICS = original_topics


def test_generate_random_survey_title_has_no_number_when_unique():
    sample_data.save_survey = lambda survey: None
    original_topics = sample_data._TOPICS
    sample_data._TOPICS = ["Travel Plans"]
    try:
        sample_data.list_surveys = lambda: [{"id": "srv_rand_1", "title": "Something Else"}]
        survey = sample_data.generate_random_survey(rng=random.Random(9))
        assert survey.title == "Test Travel Plans Survey"
    finally:
        sample_data._TOPICS = original_topics


def _survey(n_questions=4):
    return Survey(
        id="srv_rand_test",
        title="T",
        questions=[Question(id=f"srv_rand_test_q{i}", type="text", text="Q") for i in range(1, n_questions + 1)],
    )


def test_generate_random_responses_saves_fully_answered_completed_responses():
    saved = []
    sample_data.save_response = lambda response: saved.append(response)
    sample_data.save_draft = lambda draft: None

    survey = _survey(4)
    sample_data.generate_random_responses(survey, n_completed=3, n_drafts=0, rng=random.Random(4))

    assert len(saved) == 3
    for response in saved:
        assert response.survey_id == survey.id
        assert len(response.answers) == 4  # every question answered


def test_generate_random_responses_saves_only_partially_answered_drafts():
    saved = []
    sample_data.save_response = lambda response: None
    sample_data.save_draft = lambda draft: saved.append(draft)

    survey = _survey(4)
    sample_data.generate_random_responses(survey, n_completed=0, n_drafts=2, rng=random.Random(5))

    assert len(saved) == 2
    for draft in saved:
        assert draft.survey_id == survey.id
        assert 0 < len(draft.answers) < 4  # genuinely partial


def test_generate_random_responses_rejects_negative_counts():
    survey = _survey(4)
    try:
        sample_data.generate_random_responses(survey, n_completed=-1, n_drafts=0)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_is_generated_survey_id_matches_only_the_recognizable_prefix():
    assert sample_data.is_generated_survey_id("srv_rand_123") is True
    assert sample_data.is_generated_survey_id("srv_886865") is False


def test_delete_all_generated_data_only_removes_surveys_with_the_prefix():
    deleted_surveys = []
    deleted_drafts = []
    sample_data.list_surveys = lambda: [
        {"id": "srv_rand_1", "title": "Random 1"},
        {"id": "srv_real_1", "title": "Real survey"},
    ]
    sample_data.list_drafts = lambda sid: [{"id": "draft_1"}] if sid == "srv_rand_1" else []
    sample_data.delete_draft = lambda sid, did: deleted_drafts.append((sid, did))
    sample_data.delete_survey = lambda sid: deleted_surveys.append(sid)

    count = sample_data.delete_all_generated_data()

    assert count == 1
    assert deleted_surveys == ["srv_rand_1"]
    assert deleted_drafts == [("srv_rand_1", "draft_1")]

"""Integration tests for src/helpers.py against real (temp) storage.

tests/test_helpers.py covers get_draft_info by monkeypatching helpers'
bound names so no real storage is touched. These tests go the other way:
they use tests/thelpers.py to populate a temp storage tree (via
thelpers.isolated_storage, so helpers' real load_survey/list_drafts calls
read it) and check get_draft_info end to end.
"""

import src.shelpers as shelpers  # type: ignore
import src.storage as storage  # type: ignore
from src.models import Draft  # type: ignore

from tests.thelpers import ( # type: ignore
    create_completed_responses,
    create_drafts,
    create_surveys,
    isolated_storage,
)


def test_get_draft_info_returns_blank_when_survey_has_no_drafts(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 4)

        assert shelpers.get_draft_info("srv_test_1") == ("", 0, 0, 0)


def test_get_draft_info_reports_a_single_partial_drafts_progress(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 4)            # srv_test_1 with 4 questions
        create_drafts("srv_test_1", 1)  # answers the first 2 of them

        title, completed, total, draft_count = shelpers.get_draft_info("srv_test_1")

        assert (title, completed, total, draft_count) == ("Test Survey 1", 2, 4, 1)


def test_get_draft_info_prefers_the_most_recently_saved_draft(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 8)            # srv_test_1 with 8 questions
        create_drafts("srv_test_1", 2)  # both answer 4 of the 8

        # A draft saved later, with different progress, must be the one
        # reported -- "current" means newest for this survey.
        late = Draft(
            id="draft_late",
            survey_id="srv_test_1",
            label="late",
            saved_at="2999-01-01T00:00:00",  # sorts after any real timestamp
            answers={"srv_test_1_q1": "only the first question"},
        )
        storage.save_draft(late)

        title, completed, total, draft_count = shelpers.get_draft_info("srv_test_1")

        assert (title, completed, total, draft_count) == ("Test Survey 1", 1, 8, 3)


def test_get_draft_info_reports_only_the_requested_surveys_own_drafts(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(2, 4)           # srv_test_1 and srv_test_2
        create_drafts("srv_test_1", 1)
        create_drafts("srv_test_2", 3)

        assert shelpers.get_draft_info("srv_test_1") == ("Test Survey 1", 2, 4, 1)
        assert shelpers.get_draft_info("srv_test_2") == ("Test Survey 2", 2, 4, 3)


def test_completed_responses_do_not_count_as_drafts(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 4)
        create_completed_responses("srv_test_1", 5)

        assert shelpers.get_draft_info("srv_test_1") == ("", 0, 0, 0)


def test_get_draft_info_returns_blank_when_survey_deleted_but_its_drafts_remain(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 4)
        create_drafts("srv_test_1", 2)
        # delete_survey removes the survey (and its responses) but leaves
        # any drafts of it behind -- get_draft_info must treat that as
        # "no current draft", not crash.
        storage.delete_survey("srv_test_1")

        assert shelpers.get_draft_info("srv_test_1") == ("", 0, 0, 0)


def test_get_draft_info_reports_a_fully_answered_draft_as_complete(tmp_path):
    with isolated_storage(tmp_path):
        create_surveys(1, 4)  # q1 text, q2 yesno, q3 likert, q4 numeric_scale
        draft = Draft(
            id="draft_full",
            survey_id="srv_test_1",
            label="full",
            saved_at="2026-01-01T00:00:00",
            answers={
                "srv_test_1_q1": "a text answer",
                "srv_test_1_q2": "Yes",
                "srv_test_1_q3": 3,
                "srv_test_1_q4": 2,
            },
        )
        storage.save_draft(draft)

        assert shelpers.get_draft_info("srv_test_1") == ("Test Survey 1", 4, 4, 1)

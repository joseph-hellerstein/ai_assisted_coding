"""Tests for the pure-ish helpers in src/helpers.py.

These monkeypatch helpers.py's own bound names (load_survey, list_drafts),
the same way tests/test_app_callbacks.py monkeypatches app.py's, so no real
storage is touched.
"""

import helpers as helpers_module  # type: ignore
from models import Survey  # type: ignore


def test_get_draft_info_returns_blank_when_no_survey_selected():
    assert helpers_module.get_draft_info(None) == ("", 0, 0, 0)


def test_get_draft_info_returns_blank_when_survey_cannot_be_loaded():
    # e.g. the survey was deleted while a draft of it still exists.
    helpers_module.load_survey = lambda sid: None

    assert helpers_module.get_draft_info("srv_1") == ("", 0, 0, 0)


def test_get_draft_info_returns_blank_when_survey_has_no_drafts():
    helpers_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])
    helpers_module.list_drafts = lambda sid: []

    assert helpers_module.get_draft_info("srv_1") == ("", 0, 0, 0)


def test_get_draft_info_reports_the_newest_drafts_progress_and_total_count():
    # "Current" is well-defined per-survey now: the newest draft for
    # *this* survey_id, plus how many drafts it has in total -- not a
    # guess made by scanning every survey for the first one with any
    # draft at all (that assumed one draft per survey, which is no longer
    # true now that a survey can have several).
    helpers_module.load_survey = lambda sid: Survey(id=sid, title="My Survey", questions=[])
    helpers_module.list_drafts = lambda sid: [
        {"id": "draft_new", "questions_completed": 2, "total_questions": 5, "saved_at": "2026-10-21T10:00:00"},
        {"id": "draft_old", "questions_completed": 1, "total_questions": 5, "saved_at": "2026-10-20T10:00:00"},
    ]

    title, completed, total, draft_count = helpers_module.get_draft_info("srv_1")

    assert title == "My Survey"
    assert completed == 2
    assert total == 5
    assert draft_count == 2

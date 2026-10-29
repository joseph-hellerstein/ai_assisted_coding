'''Helper functions for the survey app.'''
from __future__ import annotations

from storage import load_survey, list_drafts  # type: ignore


def get_draft_info(survey_id: str | None) -> tuple[str, int, int, int]:
    """Info about `survey_id`'s most recently saved draft, for the Survey
    Taker tab's hover tooltip.

    "Current" means whichever survey is selected in the Survey Taker
    tab's own dropdown right now -- the caller is responsible for passing
    that selection in; this function no longer guesses at one by scanning
    every survey (a survey could have any number of drafts, so "the"
    current draft was never well-defined that way).

    Returns (survey_title, questions_completed, total_questions,
    draft_count). survey_title is "" (and the other fields 0) when
    `survey_id` is falsy, the survey can no longer be loaded, or it has no
    saved drafts -- the caller treats that as "no current draft".
    """
    if not survey_id:
        return "", 0, 0, 0

    survey = load_survey(survey_id)
    if not survey:
        return "", 0, 0, 0

    drafts = list_drafts(survey_id)
    if not drafts:
        return "", 0, 0, 0

    newest = drafts[0]  # list_drafts sorts newest-first
    return survey.title, newest["questions_completed"], newest["total_questions"], len(drafts)
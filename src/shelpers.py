'''Helper functions for the survey app.'''
from __future__ import annotations
from typing import Optional, List

from src.storage import load_survey, list_drafts, list_surveys  # type: ignore

import subprocess


def get_draft_info(survey_id: str) -> tuple[str, int, int, int]:
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


def find_pid_on_port(port: int) -> list[str]:
    """Find the process that is using a port.

    Args:
        port (int): port of the process to find.

    Returns:
        list[str]: list of process IDs (PIDs) using the specified port.
    """
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"], capture_output=True, text=True
    )
    return result.stdout.split()

def sort_surveys_by_title(surveys: Optional[List[dict]] = None) -> List[dict]:
    """Sort a list of surveys by their title.

    Args:
        surveys (list[dict]): List of survey dictionaries.
        surveys (list[dict]): List of survey dictionaries. If None, the function will return an empty list.

    Returns:
        list[dict]: Sorted list of survey dictionaries.
    """
    if surveys is None:
        surveys = list_surveys()
    return sorted(surveys, key=lambda x: x["title"].lower())
"""Helpers for populating survey data in tests.

Companion to the "populate the survey data for testing" item in todo.md:
quickly create surveys, completed responses, and partially-completed drafts,
and read back per-survey statistics.

Usage from a pytest test file (pytest puts tests/ on sys.path, so the module
imports as plain `thelpers`):

    from thelpers import (
        create_surveys,
        create_completed_responses,
        create_drafts,
        get_survey_statistics,
        isolated_storage,
    )

Every function takes an optional `base_dir`. When given (e.g. pytest's
`tmp_path`), storage's directories are temporarily redirected there, so the
app's real data in surveys/ and data/ is never touched. When omitted, the
functions operate on the app's actual storage directories.

When testing app code that reads storage directly (e.g. src/helpers.py),
wrap the whole scenario in `isolated_storage(tmp_path)` instead, so that
code sees the same temp data:

    with isolated_storage(tmp_path):
        create_surveys(1, 4)
        get_draft_info("srv_test_1")

Note: this module is deliberately named `thelpers` (not `helpers`) so it
cannot shadow src/helpers.py, which app.py imports as a top-level module.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

# Make src/ importable even when this module is used outside pytest
# (tests/conftest.py does the same for test modules).
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.models import Draft, Question, Response, Survey  # type: ignore
import src.storage as storage  # type: ignore


# Cycled in order when generating questions, so a survey with enough
# questions exercises every supported type.
QUESTION_TYPES = [
    "text", "yesno", "likert", "numeric_scale",
    "checkbox", "multiselect", "ranking", "matrix",
]


@contextmanager
def isolated_storage(base_dir: Path | str | None) -> Iterator[None]:
    """Point storage's directories at `base_dir` for the duration of a block.

    Mirrors the layout storage.py uses relative to the repo root
    (surveys/, data/responses/, data/drafts/); the original directories are
    restored on exit. Use it when testing app code that reads storage
    directly (e.g. src/helpers.py) so that code sees the same temp data the
    create_* functions wrote:

        with isolated_storage(tmp_path):
            create_surveys(1, 4)
            get_draft_info("srv_test_1")

    The create_* / get_survey_statistics functions apply this themselves
    when given `base_dir`, so inside an isolated_storage block the base_dir
    argument can be omitted.
    """
    if base_dir is None:
        yield
        return
    original = (storage.SURVEYS_DIR, storage.RESPONSES_DIR, storage.DRAFTS_DIR)
    try:
        base = Path(base_dir)
        storage.SURVEYS_DIR = base / "surveys"
        storage.RESPONSES_DIR = base / "data" / "responses"
        storage.DRAFTS_DIR = base / "data" / "drafts"
        storage.ensure_dirs()
        yield
    finally:
        storage.SURVEYS_DIR, storage.RESPONSES_DIR, storage.DRAFTS_DIR = original


def _make_question(qid: str, qtype: str) -> Question:
    """Build a question of `qtype` with plausible options/scale/matrix data."""
    question = Question(id=qid, type=qtype, text=f"Sample {qtype} question ({qid})")
    if qtype in ("checkbox", "multiselect"):
        question.options = [f"Option {i}" for i in (1, 2, 3)]
    elif qtype == "ranking":
        question.options = [f"Item {i}" for i in (1, 2, 3)]
    elif qtype == "likert":
        question.scale_label_min = "Strongly disagree"
        question.scale_label_max = "Strongly agree"
    elif qtype == "matrix":
        question.matrix_rows = ["Row A", "Row B"]
        question.matrix_cols = ["Low", "Medium", "High"]
    return question


def _answer_for(question: Question) -> dict[str, Any]:
    """A valid completed answer for one question.

    Values match what the Survey Taker form produces (see
    survey_taker._render_question_input), keyed exactly like
    Response.answers / Draft.answers (matrix rows use the composite
    f"{question_id}_matrix_{row}" keys).
    """
    if question.type == "text":
        return {question.id: f"Sample answer for {question.id}"}
    if question.type == "yesno":
        return {question.id: "Yes"}
    if question.type in ("likert", "numeric_scale"):
        return {question.id: (question.scale_min + question.scale_max) // 2}
    if question.type in ("checkbox", "multiselect"):
        return {question.id: list(question.options[:2])}
    if question.type == "ranking":
        return {question.id: list(question.options)}  # all items, in order
    if question.type == "matrix":
        return {
            f"{question.id}_matrix_{row}": question.matrix_cols[0]
            for row in question.matrix_rows
        }
    raise ValueError(f"Unknown question type: {question.type!r}")


def create_surveys(
    n: int,
    m: int = 3,
    prefix: str = "srv_test",
    base_dir: Path | str | None = None,
) -> list[Survey]:
    """Create n surveys with m questions each and return the Survey objects.

    Survey ids are f"{prefix}_1" .. f"{prefix}_{n}" (deterministic, so
    re-running is idempotent); question ids are f"{survey_id}_q{j}". Question
    types cycle through QUESTION_TYPES, so a survey with m >= 8 questions
    contains one of every type.
    """
    if n < 0 or m < 0:
        raise ValueError("n and m must be non-negative")
    with isolated_storage(base_dir):
        created = []
        for i in range(1, n + 1):
            survey_id = f"{prefix}_{i}"
            questions = [
                _make_question(
                    f"{survey_id}_q{j}",
                    QUESTION_TYPES[(j - 1) % len(QUESTION_TYPES)],
                )
                for j in range(1, m + 1)
            ]
            survey = Survey(
                id=survey_id,
                title=f"Test Survey {i}",
                description=(
                    f"Auto-generated test survey with "
                    f"{m} question{'s' if m != 1 else ''}"
                ),
                questions=questions,
            )
            storage.save_survey(survey)
            created.append(survey)
        return created


def create_completed_responses(
    survey_id: str,
    n: int,
    prefix: str = "resp_test",
    base_dir: Path | str | None = None,
) -> list[Response]:
    """Create n fully completed responses for `survey_id` and return them.

    Every question in the survey gets a valid answer (see _answer_for), so
    form_logic.count_completed_questions() reports all questions answered.
    Response ids are f"{prefix}_1" .. f"{prefix}_{n}"; submitted_at values
    are spaced one minute apart (response n is the most recent).

    Raises ValueError if `survey_id` does not exist in storage.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    with isolated_storage(base_dir):
        survey = storage.load_survey(survey_id)
        if survey is None:
            raise ValueError(f"Unknown survey id: {survey_id!r}")
        now = datetime.now()
        created = []
        for i in range(1, n + 1):
            answers: dict[str, Any] = {}
            for question in survey.questions:
                answers.update(_answer_for(question))
            response = Response(
                id=f"{prefix}_{i}",
                survey_id=survey_id,
                submitted_at=(now - timedelta(minutes=n - i)).isoformat(),
                answers=answers,
            )
            storage.save_response(response)
            created.append(response)
        return created


def create_drafts(
    survey_id: str,
    n: int,
    prefix: str = "draft_test",
    base_dir: Path | str | None = None,
) -> list[Draft]:
    """Create n partially completed drafts for `survey_id` and return them.

    Each draft answers the first len(questions) // 2 of the survey's
    questions (always strictly fewer than all of them, even for a
    one-question survey), so every draft is genuinely partial. Draft ids are
    f"{prefix}_1" .. f"{prefix}_{n}", labels "Test draft i", and saved_at
    values are spaced one minute apart (draft n is the most recent).

    Raises ValueError if `survey_id` does not exist in storage.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    with isolated_storage(base_dir):
        survey = storage.load_survey(survey_id)
        if survey is None:
            raise ValueError(f"Unknown survey id: {survey_id!r}")
        answered_count = len(survey.questions) // 2
        now = datetime.now()
        created = []
        for i in range(1, n + 1):
            answers: dict[str, Any] = {}
            for question in survey.questions[:answered_count]:
                answers.update(_answer_for(question))
            draft = Draft(
                id=f"{prefix}_{i}",
                survey_id=survey_id,
                label=f"Test draft {i}",
                saved_at=(now - timedelta(minutes=n - i)).isoformat(),
                answers=answers,
            )
            storage.save_draft(draft)
            created.append(draft)
        return created


def get_survey_statistics(base_dir: Path | str | None = None) -> dict[str, dict]:
    """Per-survey statistics over everything currently in storage.

    Returns {survey_id: {"title": str, "completed": [Response, ...],
    "drafts": [Draft, ...]}} for every saved survey (a survey with no
    responses or drafts gets empty lists). Counts are len() of the two
    lists.
    """
    with isolated_storage(base_dir):
        stats: dict[str, dict] = {}
        for info in storage.list_surveys():
            survey_id = info["id"]
            stats[survey_id] = {
                "title": info["title"],
                "completed": storage.load_responses(survey_id),
                "drafts": [
                    storage.load_draft(survey_id, draft["id"])
                    for draft in storage.list_drafts(survey_id)
                ],
            }
        return stats

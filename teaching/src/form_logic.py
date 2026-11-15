"""Pure helpers used by the callbacks. No Dash, no files, so they're easy to test."""
from __future__ import annotations

from typing import Any

from src.models import Question, generate_id

CHECKBOX_MIN_OPTIONS = 2


def _clean_options(options_text: str | None) -> list[str]:
    """One option per line: strip each, drop blanks and repeats, keep the order."""
    options = []
    for line in (options_text or "").splitlines():
        option = line.strip()
        if option and option not in options:
            options.append(option)
    return options


def assemble_questions_from_state(
    types: list[str | None],
    texts: list[str | None],
    options_texts: list[str | None],
) -> tuple[list[Question], list[str]]:
    """Turn the Survey Maker's question rows into Questions.

    The three lists are parallel: entry i describes row i. Returns
    (questions, []) if every row is valid, or ([], errors) otherwise,
    where each error reads "Question N: ..." (N counts rows from 1).
    """
    questions, errors = [], []
    for row, (qtype, text, options_text) in enumerate(zip(types, texts, options_texts), start=1):
        text = (text or "").strip()
        if not text:
            continue  # a blank row is skipped
        qtype = qtype or "text"
        options = _clean_options(options_text) if qtype == "checkbox" else []
        if qtype == "checkbox" and len(options) < CHECKBOX_MIN_OPTIONS:
            errors.append(f"Question {row}: a checkbox question needs at least 2 options.")
            continue
        questions.append(Question(id=generate_id("q_"), type=qtype, text=text, options=options))

    if errors:
        return [], errors
    if not questions:
        return [], ["Add at least one question."]
    return questions, []


def is_valid_respondent_id(value: str | None) -> bool:
    """True only for exactly 5 digits, e.g. "01234"."""
    return value is not None and len(value) == 5 and value.isascii() and value.isdigit()


def build_response_answers(qids: list[str], values: list) -> dict[str, Any]:
    """Map each question id to its answer, leaving out unanswered questions."""
    answers = {}
    for qid, value in zip(qids, values):
        if isinstance(value, str):
            value = value.strip()
        if value in (None, "", []):
            continue
        answers[qid] = value
    return answers

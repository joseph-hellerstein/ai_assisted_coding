"""Sample/test data generation for the landing page's "Test" panel.

Lets anyone populate the app with a throwaway random survey plus
completed/draft responses for it, without building a survey by hand --
and clean all of it back out again with one click. Generated surveys,
responses, and drafts are saved through the same storage functions (and so
live in the same surveys/ and data/ directories) as anything a real user
creates; the only thing that marks a survey as generated is its id prefix
(RANDOM_SURVEY_ID_PREFIX), which delete_all_generated_data() uses to find
them again.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from src.models import Draft, Question, Response, Survey, generate_id  # type: ignore
from src.storage import (  # type: ignore
    delete_draft,
    delete_survey,
    list_drafts,
    list_surveys,
    save_draft,
    save_response,
    save_survey,
)

RANDOM_SURVEY_ID_PREFIX = "srv_rand_"

QUESTION_TYPES = [
    "text", "yesno", "likert", "numeric_scale",
    "checkbox", "multiselect", "ranking", "matrix",
]

_TOPICS = [
    "Coffee Preferences", "Remote Work", "Favorite Snacks", "Team Offsite",
    "Weekend Hobbies", "Office Setup", "Travel Plans", "Reading Habits",
]


def _make_question(qid: str, qtype: str, rng: random.Random) -> Question:
    """Build a question of `qtype` with plausible, randomized options."""
    question = Question(id=qid, type=qtype, text=f"Sample {qtype.replace('_', ' ')} question")
    question.required = rng.choice([True, False])
    if qtype in ("checkbox", "multiselect", "ranking"):
        question.options = [f"Option {i}" for i in range(1, rng.randint(3, 5))]
    elif qtype == "likert":
        question.scale_label_min = "Strongly disagree"
        question.scale_label_max = "Strongly agree"
    elif qtype == "matrix":
        question.matrix_rows = [f"Row {i}" for i in range(1, rng.randint(2, 4))]
        question.matrix_cols = ["Low", "Medium", "High"]
    return question


def _answer_for(question: Question, rng: random.Random) -> dict[str, Any]:
    """A valid, randomized answer for one question.

    Keyed exactly like Response.answers / Draft.answers (matrix rows use
    the composite f"{question_id}_matrix_{row}" keys) -- see
    survey_taker._render_question_input for the shape this mirrors.
    """
    if question.type == "text":
        return {question.id: f"Random answer {rng.randint(1, 1000)}"}
    if question.type == "yesno":
        return {question.id: rng.choice(["Yes", "No"])}
    if question.type in ("likert", "numeric_scale"):
        return {question.id: rng.randint(question.scale_min, question.scale_max)}
    if question.type in ("checkbox", "multiselect"):
        return {question.id: rng.sample(question.options, rng.randint(1, len(question.options)))}
    if question.type == "ranking":
        shuffled = list(question.options)
        rng.shuffle(shuffled)
        return {question.id: shuffled}
    if question.type == "matrix":
        return {
            f"{question.id}_matrix_{row}": rng.choice(question.matrix_cols)
            for row in question.matrix_rows
        }
    raise ValueError(f"Unknown question type: {question.type!r}")


def _unique_test_title(base_title: str) -> str:
    """`base_title`, or `base_title` with the lowest number (starting at 2)
    not already used by an existing survey's title -- so repeated
    generation produces "Test X Survey", "Test X Survey 2", "Test X Survey
    3", etc. instead of several surveys sharing one indistinguishable name.
    """
    existing_titles = {s["title"] for s in list_surveys()}
    if base_title not in existing_titles:
        return base_title
    n = 2
    while f"{base_title} {n}" in existing_titles:
        n += 1
    return f"{base_title} {n}"


def generate_random_survey(rng: random.Random | None = None) -> Survey:
    """Build and save one new random survey (3-8 questions, cycling
    through every supported question type) and return it.

    The title always starts with "Test " and is deduplicated against
    every existing survey's title (see _unique_test_title), so generated
    surveys are easy to recognize and tell apart in the Maker/Taker/
    Analyzer dropdowns and hovers.
    """
    rng = rng or random.Random()
    survey_id = generate_id(RANDOM_SURVEY_ID_PREFIX)
    topic = rng.choice(_TOPICS)
    n_questions = rng.randint(3, 8)
    questions = [
        _make_question(f"{survey_id}_q{i}", QUESTION_TYPES[(i - 1) % len(QUESTION_TYPES)], rng)
        for i in range(1, n_questions + 1)
    ]
    survey = Survey(
        id=survey_id,
        title=_unique_test_title(f"Test {topic} Survey"),
        description=f"Randomly generated test survey about {topic.lower()}.",
        questions=questions,
    )
    save_survey(survey)
    return survey


def generate_random_responses(
    survey: Survey,
    n_completed: int,
    n_drafts: int,
    rng: random.Random | None = None,
) -> None:
    """Save `n_completed` fully-answered Responses and `n_drafts`
    partially-answered Drafts (each answering the first half of the
    survey's questions) for `survey`.
    """
    if n_completed < 0 or n_drafts < 0:
        raise ValueError("n_completed and n_drafts must be non-negative")
    rng = rng or random.Random()
    now = datetime.now()

    for i in range(n_completed):
        answers: dict[str, Any] = {}
        for question in survey.questions:
            answers.update(_answer_for(question, rng))
        save_response(Response(
            id=generate_id("resp_"),
            survey_id=survey.id,
            submitted_at=(now - timedelta(minutes=n_completed - i)).isoformat(),
            answers=answers,
        ))

    answered_count = len(survey.questions) // 2
    for i in range(n_drafts):
        answers = {}
        for question in survey.questions[:answered_count]:
            answers.update(_answer_for(question, rng))
        save_draft(Draft(
            id=generate_id("draft_"),
            survey_id=survey.id,
            label="",
            saved_at=(now - timedelta(minutes=n_drafts - i)).isoformat(),
            answers=answers,
        ))


def is_generated_survey_id(survey_id: str) -> bool:
    """Whether `survey_id` belongs to a survey this module generated."""
    return survey_id.startswith(RANDOM_SURVEY_ID_PREFIX)


def delete_all_generated_data() -> int:
    """Delete every survey this module generated, along with its
    responses and drafts (delete_survey alone leaves drafts behind).

    Returns how many surveys were removed.
    """
    generated_ids = [s["id"] for s in list_surveys() if is_generated_survey_id(s["id"])]
    for survey_id in generated_ids:
        for draft in list_drafts(survey_id):
            delete_draft(survey_id, draft["id"])
        delete_survey(survey_id)
    return len(generated_ids)

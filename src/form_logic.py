"""Pure helper functions for assembling Survey Maker / Taker form data.

These are kept free of any Dash/DOM dependency so the core data-assembly
logic (the part responsible for not losing what a user typed) can be
tested directly, without going through a running Dash server.
"""
from __future__ import annotations

from datetime import datetime

from models import Question  # type: ignore


def lines_to_list(text: str | None) -> list[str]:
    """Split newline-separated textarea text into a list of stripped, non-blank lines."""
    if not text:
        return []
    return [line.strip() for line in text.split("\n") if line.strip()]


def list_to_lines(items: list[str] | None) -> str:
    """Join a list of strings into newline-separated textarea text."""
    return "\n".join(items or [])


def type_visibility(question_type: str) -> dict:
    """Which type-specific editor sections should be visible for a question type."""
    return {
        "options": question_type in ("checkbox", "multiselect", "ranking"),
        "scale": question_type in ("likert", "numeric_scale"),
        "matrix": question_type == "matrix",
    }


SECTION_STYLE_EXTRA = {"marginLeft": "20px", "marginTop": "5px"}


def section_style(visible: bool) -> dict:
    """Style for a type-specific editor section: same layout, toggled display.

    Used both at initial render and by the type-change callback, so a
    question's options/scale/matrix sections are shown or hidden without
    ever being rebuilt (and therefore without ever losing their contents).
    """
    style = dict(SECTION_STYLE_EXTRA)
    style["display"] = "block" if visible else "none"
    return style


def extract_clicked_qid(triggered_id, triggered_value) -> str | None:
    """Resolve a genuine click on a {"type": ..., "qid": ...} pattern-matching
    button from Dash's callback_context triggered id/value.

    Pattern-matching ALL-Input callbacks also fire when the *set* of matched
    components changes (e.g. a new button mounts after Add Question) even
    though nothing was clicked; in that case the reported value is falsy
    (0/None), which this rejects.
    """
    if not isinstance(triggered_id, dict):
        return None
    if not triggered_value:
        return None
    return triggered_id.get("qid")


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def assemble_questions_from_state(
    qids: list[str],
    types: list[str],
    texts: list[str],
    requireds: list[list],
    options_texts: list[str],
    scale_mins: list,
    scale_maxs: list,
    scale_label_mins: list[str],
    scale_label_maxs: list[str],
    matrix_rows_texts: list[str],
    matrix_cols_texts: list[str],
) -> list[Question]:
    """Build Question objects from the live values of the rendered form fields.

    `qids` is the ordering/identity key (each question's stable id); every
    other argument is a parallel list of that field's current value for the
    same question, in the same order.
    """
    questions = []
    for i, qid in enumerate(qids):
        questions.append(Question(
            id=qid,
            type=types[i],
            text=texts[i] or "",
            required=bool(requireds[i]),
            options=lines_to_list(options_texts[i]),
            scale_min=_to_int(scale_mins[i], 1),
            scale_max=_to_int(scale_maxs[i], 5),
            scale_label_min=scale_label_mins[i] or "",
            scale_label_max=scale_label_maxs[i] or "",
            matrix_rows=lines_to_list(matrix_rows_texts[i]),
            matrix_cols=lines_to_list(matrix_cols_texts[i]),
        ))
    return questions


def _wrapper_qid(child) -> str | None:
    try:
        cid = child["props"]["id"]
    except (TypeError, KeyError):
        return None
    if isinstance(cid, dict):
        return cid.get("qid")
    return None


def remove_question_by_qid(children: list | None, qid: str) -> list:
    """Remove the question editor subtree whose wrapper id matches `qid`.

    `children` is the raw list of already-rendered child components (as
    received via a Dash State on a container's "children" prop), left
    untouched for every entry except the one being removed.
    """
    if not children:
        return []
    return [child for child in children if _wrapper_qid(child) != qid]


def build_response_answers_from_state(qids: list[str], values: list) -> dict:
    """Build a Response.answers dict from parallel answer-id/value lists.

    A matrix sub-answer's qid is the composite "{question_id}::{row_label}"
    (so a single pattern-matching id type covers both plain and matrix
    answers); it is split back into the f"{question_id}_matrix_{row_label}"
    key format the Analyzer already expects.
    """
    answers = {}
    for qid, value in zip(qids, values):
        if "::" in qid:
            base_qid, row = qid.split("::", 1)
            answers[f"{base_qid}_matrix_{row}"] = value
        else:
            answers[qid] = value
    return answers


def answer_value_for_qid(answers: dict, qid: str):
    """Look up the saved value for an answer field's qid in a Draft/Response
    answers dict, inverting build_response_answers_from_state's key mapping.

    Used to prefill a resumed draft's form fields: a plain qid is looked up
    directly, a matrix row's composite qid ("question_id::row") is looked up
    under its f"{question_id}_matrix_{row}" key.
    """
    if "::" in qid:
        base_qid, row = qid.split("::", 1)
        return answers.get(f"{base_qid}_matrix_{row}")
    return answers.get(qid)


def _is_answered(value) -> bool:
    """A value counts as answered unless it's missing/empty; a literal 0
    (e.g. a numeric_scale answer) must still count, unlike a plain truthy
    check would treat it."""
    return value not in (None, "", [])


def count_completed_questions(questions: list[Question], answers: dict) -> int:
    """How many of `questions` have a real answer in a Draft/Response
    answers dict. A matrix question counts as completed only once every
    one of its rows has an answer; every other type is a single lookup.
    """
    completed = 0
    for q in questions:
        if q.type == "matrix":
            if q.matrix_rows and all(_is_answered(answers.get(f"{q.id}_matrix_{row}")) for row in q.matrix_rows):
                completed += 1
        elif _is_answered(answers.get(q.id)):
            completed += 1
    return completed


def draft_option_label(
    label: str | None,
    saved_at: str,
    questions_completed: int | None = None,
    total_questions: int | None = None,
) -> str:
    """Label shown for a saved draft in the resume dropdown.

    Uses the user-supplied label if they gave one, otherwise falls back to
    a formatted save timestamp so every draft is still distinguishable.
    Appends "(N/M answered)" whenever both counts are available (they
    won't be if the survey itself could no longer be loaded).
    """
    base = label if label else "Saved " + datetime.fromisoformat(saved_at).strftime("%Y-%m-%d %H:%M:%S")
    if questions_completed is None or total_questions is None:
        return base
    return f"{base} ({questions_completed}/{total_questions} answered)"

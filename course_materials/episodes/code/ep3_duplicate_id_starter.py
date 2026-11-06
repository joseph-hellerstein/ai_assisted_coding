"""Episode 3 starter code: "Check for duplicate survey taker ID."

This is deliberately flawed. It represents what an AI assistant might hand
back on a first pass if asked to add duplicate-id rejection to Survey
Taker's respondent_id field (see Survey.respondent_id / is_valid_respondent_id
in the main app). It is NOT meant to be merged anywhere -- it's the artifact
students review in the episode 3 exercise, using an AI-assisted code review.

Drop this into the student starter repo as form_logic.py's
has_duplicate_respondent_id, plus the submit_survey_response excerpt below
wired into app.py, both marked #A2# the same way episode 2 used #A1# for
the hover feature.

Context students have at this point: episode 2 (control flow/callbacks,
the Survey/Response/Draft data model, reading storage.py directly). They do
NOT yet have a unit-testing episode (that's episode 4) -- this review is
meant to be done by reading, tracing, and reasoning about the code, with an
AI assistant's help, not by running a test suite against it.
"""
from __future__ import annotations

from src.storage import load_responses  # type: ignore


def has_duplicate_respondent_id(survey_id: str, respondent_id: str) -> bool:
    """Whether another response to this survey already used respondent_id."""
    responses = load_responses(survey_id)
    return any(r.id == respondent_id for r in responses)


# --- Excerpt: how it gets wired into app.py's submit_survey_response ---
#
# The real callback (src/app.py) already validates survey_id and guards the
# spurious n_clicks=0 mount event; this excerpt picks up right after that,
# where the real submit_survey_response checks is_valid_respondent_id.
#
#     if has_duplicate_respondent_id(survey_id, respondent_id):
#         return (
#             html.Span("⚠️ That ID has already been used for this survey.", style={"color": "orange"}),
#             no_update, no_update, no_update, no_update,
#         )
#     if not is_valid_respondent_id(respondent_id):
#         return (
#             html.Span("⚠️ Your ID must be exactly 5 digits.", style={"color": "orange"}),
#             no_update, no_update, no_update, no_update,
#         )
#
#     qids = [d["qid"] for d in ids]
#     answers = build_response_answers_from_state(qids, values)
#     response = Response(
#         id=generate_id("resp_"),
#         survey_id=survey_id,
#         submitted_at=datetime.now().isoformat(),
#         answers=answers,
#         respondent_id=respondent_id,
#     )
#     save_response(response)


# ===========================================================================
# INSTRUCTOR NOTES -- do not hand this section to students before the
# exercise. Two bugs are intentionally present; a third point is a design
# question raised verbally, not a code bug.
# ===========================================================================
#
# BUG 1 (inside has_duplicate_respondent_id): compares `r.id` instead of
# `r.respondent_id`. `r.id` is the internally generated response id
# (generate_id("resp_...")), which is unique by construction -- so this
# comparison can never be True for a real duplicate. The function always
# returns False. It LOOKS plausible (both fields are named "id" something),
# and nothing about running the app surfaces this -- you have to read what
# `r.id` actually is to catch it. This is the headline finding a code
# review (AI or human) should produce.
#
# BUG 2 (at the call site): the duplicate check runs BEFORE
# is_valid_respondent_id. Combine this with bug 1's irrelevance and a
# subtler failure shows up: any blank/legacy respondent_id ("" -- every
# response saved before this field existed, and everything sample_data.py
# generates, defaults to "") would, if bug 1 were fixed naively to compare
# `r.respondent_id`, make *every* blank-id response collide with every other
# blank-id response the instant someone submits with an empty id field --
# rejected as "already used" instead of the real problem, "not 5 digits."
# Ordering matters: format must be validated before uniqueness is checked.
#
# DESIGN QUESTION (not a bug in this code -- raise it as discussion):
# has_duplicate_respondent_id scopes the check to one survey
# (load_responses(survey_id)). Is that the right scope, or should a
# respondent's id be unique across every survey? The spec doesn't say.
# Nothing here is "wrong" either way, but a good review calls this out as
# an assumption worth confirming rather than silently picking one.
#
# Suggested flow: students get this file + the excerpt with NO notes,
# spend ~5 min reading/tracing it against load_responses/Response in the
# real repo, then run an AI-assisted review pass and compare what it finds
# against bugs 1-2 above. The design question is a good one to ask the room
# directly if the AI's review doesn't raise it unprompted.

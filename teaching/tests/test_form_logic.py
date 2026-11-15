import pytest

from src.form_logic import assemble_questions_from_state, build_response_answers, is_valid_respondent_id

CHECKBOX_ERROR = "a checkbox question needs at least 2 options."


def test_assemble_skips_blank_and_whitespace_rows_and_keeps_row_order():
    qs, errors = assemble_questions_from_state(
        ["text", "yesno", "checkbox", "text", None],
        ["  Name?  ", "   ", "Colors?", None, "Why?"],
        ["", "", "Red\n\n Blue \nRed", "", "ignored"],
    )
    assert errors == []
    assert [(q.type, q.text, q.options) for q in qs] == [
        ("text", "Name?", []), ("checkbox", "Colors?", ["Red", "Blue"]), ("text", "Why?", []),
    ]
    assert len({q.id for q in qs}) == 3


def test_assemble_ignores_options_for_text_and_yesno():
    qs, errors = assemble_questions_from_state(["yesno", "text"], ["Attended?", "Why?"], ["a\nb", "c\nd"])
    assert errors == []
    assert [q.options for q in qs] == [[], []]


def test_assemble_reports_every_bad_checkbox_row():
    qs, errors = assemble_questions_from_state(
        ["text", "checkbox", "text", "checkbox"],
        ["Name?", "Pick one", "Why?", "Pick again"],
        ["", "Only one", "", "Red\nRed"],
    )
    assert qs == []
    assert errors == [f"Question 2: {CHECKBOX_ERROR}", f"Question 4: {CHECKBOX_ERROR}"]


def test_assemble_all_blank_form():
    assert assemble_questions_from_state(["text"] * 5, ["", "  ", None, "", ""], [""] * 5) == (
        [], ["Add at least one question."],
    )


@pytest.mark.parametrize("value, expected", [
    ("12345", True), ("1234", False), ("123456", False), ("12a45", False),
    (" 1234", False), ("", False), (None, False),
])
def test_is_valid_respondent_id(value, expected):
    assert is_valid_respondent_id(value) is expected


def test_build_response_answers_omits_unanswered_and_strips_text():
    assert build_response_answers(["q1", "q2", "q3", "q4"], ["  hi ", None, [], ["Red"]]) == {
        "q1": "hi", "q4": ["Red"],
    }

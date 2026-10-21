"""Unit tests for the pure form-assembly helpers used by the Survey Maker
and Survey Taker callbacks (src/form_logic.py)."""

from form_logic import (  # type: ignore
    lines_to_list,
    list_to_lines,
    type_visibility,
    section_style,
    extract_clicked_qid,
    assemble_questions_from_state,
    remove_question_by_qid,
    build_response_answers_from_state,
    answer_value_for_qid,
    draft_option_label,
    count_completed_questions,
)
from models import Question  # type: ignore


def test_lines_to_list_splits_and_strips_blank_lines():
    text = "Option A\n  Option B  \n\nOption C\n"
    assert lines_to_list(text) == ["Option A", "Option B", "Option C"]


def test_lines_to_list_empty_text_returns_empty_list():
    assert lines_to_list("") == []
    assert lines_to_list(None) == []


def test_list_to_lines_joins_with_newline():
    assert list_to_lines(["A", "B", "C"]) == "A\nB\nC"


def test_list_to_lines_empty_list_returns_empty_string():
    assert list_to_lines([]) == ""
    assert list_to_lines(None) == ""


def test_type_visibility_options_types():
    for qtype in ("checkbox", "multiselect", "ranking"):
        v = type_visibility(qtype)
        assert v == {"options": True, "scale": False, "matrix": False}, qtype


def test_type_visibility_scale_types():
    for qtype in ("likert", "numeric_scale"):
        v = type_visibility(qtype)
        assert v == {"options": False, "scale": True, "matrix": False}, qtype


def test_type_visibility_matrix_type():
    assert type_visibility("matrix") == {"options": False, "scale": False, "matrix": True}


def test_type_visibility_plain_types_show_nothing_extra():
    for qtype in ("text", "yesno"):
        v = type_visibility(qtype)
        assert v == {"options": False, "scale": False, "matrix": False}, qtype


def test_assemble_questions_from_state_preserves_qid_and_captures_live_text():
    # This is the regression test for the original bug: what the user
    # actually typed into the question fields must end up in the saved
    # Question objects, keyed by the question's stable id.
    questions = assemble_questions_from_state(
        qids=["q_1", "q_2"],
        types=["text", "checkbox"],
        texts=["How satisfied are you?", "Pick your favorites"],
        requireds=[["req"], []],
        options_texts=["", "Red\nGreen\nBlue"],
        scale_mins=[1, 1],
        scale_maxs=[5, 5],
        scale_label_mins=["", ""],
        scale_label_maxs=["", ""],
        matrix_rows_texts=["", ""],
        matrix_cols_texts=["", ""],
    )

    assert len(questions) == 2

    q1 = questions[0]
    assert q1.id == "q_1"
    assert q1.type == "text"
    assert q1.text == "How satisfied are you?"
    assert q1.required is True
    assert q1.options == []

    q2 = questions[1]
    assert q2.id == "q_2"
    assert q2.text == "Pick your favorites"
    assert q2.required is False
    assert q2.options == ["Red", "Green", "Blue"]


def test_assemble_questions_from_state_parses_scale_and_matrix_fields():
    questions = assemble_questions_from_state(
        qids=["q_1"],
        types=["likert"],
        texts=["Rate it"],
        requireds=[["req"]],
        options_texts=[""],
        scale_mins=[1],
        scale_maxs=[7],
        scale_label_mins=["Disagree"],
        scale_label_maxs=["Agree"],
        matrix_rows_texts=[""],
        matrix_cols_texts=[""],
    )
    q = questions[0]
    assert q.scale_min == 1
    assert q.scale_max == 7
    assert q.scale_label_min == "Disagree"
    assert q.scale_label_max == "Agree"


def test_assemble_questions_from_state_parses_matrix_rows_and_cols():
    questions = assemble_questions_from_state(
        qids=["q_1"],
        types=["matrix"],
        texts=["Rate each item"],
        requireds=[[]],
        options_texts=[""],
        scale_mins=[1],
        scale_maxs=[5],
        scale_label_mins=[""],
        scale_label_maxs=[""],
        matrix_rows_texts=["Speed\nQuality"],
        matrix_cols_texts=["Poor\nGood\nGreat"],
    )
    q = questions[0]
    assert q.matrix_rows == ["Speed", "Quality"]
    assert q.matrix_cols == ["Poor", "Good", "Great"]


def test_remove_question_by_qid_removes_only_matching_entry():
    children = [
        {"type": "Div", "namespace": "dash_html_components",
         "props": {"id": {"type": "q-wrapper", "qid": "q_1"}, "children": ["first"]}},
        {"type": "Div", "namespace": "dash_html_components",
         "props": {"id": {"type": "q-wrapper", "qid": "q_2"}, "children": ["second"]}},
        {"type": "Div", "namespace": "dash_html_components",
         "props": {"id": {"type": "q-wrapper", "qid": "q_3"}, "children": ["third"]}},
    ]

    result = remove_question_by_qid(children, "q_2")

    assert [c["props"]["id"]["qid"] for c in result] == ["q_1", "q_3"]


def test_remove_question_by_qid_leaves_other_entries_untouched():
    # Regression guard: deleting one question must not alter the
    # (already-live-edited) content of any other question's subtree.
    children = [
        {"type": "Div", "namespace": "dash_html_components",
         "props": {"id": {"type": "q-wrapper", "qid": "q_1"}, "children": ["kept exactly as-is"]}},
        {"type": "Div", "namespace": "dash_html_components",
         "props": {"id": {"type": "q-wrapper", "qid": "q_2"}, "children": ["to be removed"]}},
    ]

    result = remove_question_by_qid(children, "q_2")

    assert len(result) == 1
    assert result[0]["props"]["children"] == ["kept exactly as-is"]


def test_remove_question_by_qid_empty_children_returns_empty_list():
    assert remove_question_by_qid([], "q_1") == []
    assert remove_question_by_qid(None, "q_1") == []


def test_section_style_visible_shows_block_display():
    style = section_style(True)
    assert style["display"] == "block"


def test_section_style_hidden_uses_none_display():
    style = section_style(False)
    assert style["display"] == "none"


def test_extract_clicked_qid_returns_qid_for_a_genuine_click():
    assert extract_clicked_qid({"type": "delete-q", "qid": "q_2"}, 1) == "q_2"


def test_extract_clicked_qid_ignores_newly_mounted_button_with_zero_clicks():
    # When a new delete button mounts (e.g. after Add Question), Dash's
    # ALL-pattern Input reports it as "triggered" even though nobody
    # clicked it; its n_clicks value is falsy (0/None) in that case.
    assert extract_clicked_qid({"type": "delete-q", "qid": "q_3"}, 0) is None
    assert extract_clicked_qid({"type": "delete-q", "qid": "q_3"}, None) is None


def test_extract_clicked_qid_ignores_non_pattern_trigger():
    assert extract_clicked_qid("maker-add-question", 1) is None
    assert extract_clicked_qid(None, 1) is None


def test_build_response_answers_from_state_maps_plain_answers_by_qid():
    answers = build_response_answers_from_state(
        qids=["q_1", "q_2"],
        values=["Yes", "Blue"],
    )
    assert answers == {"q_1": "Yes", "q_2": "Blue"}


def test_build_response_answers_from_state_splits_matrix_composite_qids():
    # Matrix answers are collected under a composite qid "qid::row" so a
    # single pattern-matching id type can cover both plain and matrix
    # answers; this must land in the same key format the Analyzer expects
    # (f"{question_id}_matrix_{row_label}").
    answers = build_response_answers_from_state(
        qids=["q_1::Speed", "q_1::Quality"],
        values=["Good", "Great"],
    )
    assert answers == {
        "q_1_matrix_Speed": "Good",
        "q_1_matrix_Quality": "Great",
    }


def test_answer_value_for_qid_returns_plain_answer_by_qid():
    assert answer_value_for_qid({"q_1": "Yes"}, "q_1") == "Yes"


def test_answer_value_for_qid_returns_none_when_missing():
    assert answer_value_for_qid({}, "q_1") is None


def test_answer_value_for_qid_resolves_matrix_composite_qid():
    # Mirrors build_response_answers_from_state's forward mapping, so a
    # resumed draft's matrix answers land back on the right row input.
    answers = {"q_9_matrix_Speed": "Good"}
    assert answer_value_for_qid(answers, "q_9::Speed") == "Good"


def test_draft_option_label_uses_label_when_present():
    assert draft_option_label("My draft", "2026-10-20T15:30:00") == "My draft"


def test_draft_option_label_falls_back_to_formatted_timestamp_when_label_blank():
    assert draft_option_label("", "2026-10-20T15:30:00") == "Saved 2026-10-20 15:30:00"


def test_draft_option_label_falls_back_to_formatted_timestamp_when_label_none():
    assert draft_option_label(None, "2026-10-20T09:05:00") == "Saved 2026-10-20 09:05:00"


def test_draft_option_label_distinguishes_drafts_saved_in_the_same_minute():
    # Several unlabeled drafts can now be saved within one sitting (see the
    # save_draft_callback fix), often within the same minute -- the label
    # needs second-level precision or they'd be indistinguishable in the
    # resume dropdown.
    a = draft_option_label("", "2026-10-20T15:30:01")
    b = draft_option_label("", "2026-10-20T15:30:47")
    assert a != b


def test_count_completed_questions_counts_plain_non_empty_answers():
    questions = [
        Question(id="q_1", type="text", text="A"),
        Question(id="q_2", type="yesno", text="B"),
    ]
    answers = {"q_1": "Some text", "q_2": "Yes"}
    assert count_completed_questions(questions, answers) == 2


def test_count_completed_questions_ignores_empty_or_missing_answers():
    questions = [
        Question(id="q_1", type="text", text="A"),
        Question(id="q_2", type="checkbox", text="B", options=["X"]),
        Question(id="q_3", type="text", text="C"),
    ]
    answers = {"q_1": "", "q_2": []}  # q_3 missing entirely
    assert count_completed_questions(questions, answers) == 0


def test_count_completed_questions_treats_zero_as_a_real_answer():
    # A literal 0 (e.g. a numeric_scale answer) must count as answered,
    # not be mistaken for "empty" the way a falsy check would.
    questions = [Question(id="q_1", type="numeric_scale", text="A", scale_min=0, scale_max=5)]
    answers = {"q_1": 0}
    assert count_completed_questions(questions, answers) == 1


def test_draft_option_label_appends_progress_when_available():
    label = draft_option_label("My draft", "2026-10-20T15:30:00", questions_completed=2, total_questions=5)
    assert label == "My draft (2/5 answered)"


def test_draft_option_label_omits_progress_when_unavailable():
    # e.g. the survey itself could no longer be loaded to count against.
    label = draft_option_label("My draft", "2026-10-20T15:30:00", questions_completed=None, total_questions=None)
    assert label == "My draft"


def test_count_completed_questions_requires_every_matrix_row_answered():
    q = Question(id="q_1", type="matrix", text="Rate these",
                 matrix_rows=["Speed", "Quality"], matrix_cols=["Poor", "Good"])

    partially_answered = {"q_1_matrix_Speed": "Good"}
    assert count_completed_questions([q], partially_answered) == 0

    fully_answered = {"q_1_matrix_Speed": "Good", "q_1_matrix_Quality": "Poor"}
    assert count_completed_questions([q], fully_answered) == 1

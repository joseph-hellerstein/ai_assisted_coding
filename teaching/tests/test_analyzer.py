from dash import dcc

from src.app import analyze_survey
from src.models import Question, Response, Survey
from src.storage import save_response, save_survey
from src.survey_analyzer import build_results, question_chart, response_table, word_counts

TEXT_Q = Question(id="q_text", type="text", text="Comments?")
YESNO_Q = Question(id="q_yn", type="yesno", text="Attended?")
CHECKBOX_Q = Question(id="q_cb", type="checkbox", text="Colors?", options=["Red", "Blue", "Green"])
SURVEY = Survey(id="srv_demo", title="Demo", questions=[TEXT_Q, YESNO_Q, CHECKBOX_Q])


def _response(n, answers):
    return Response(id=f"resp_{n}", survey_id="srv_demo", submitted_at=f"2026-01-0{n}T00:00:00",
                    respondent_id=f"0000{n}", answers=answers)


def _graphs(tree):
    return [c for c in tree._traverse() if isinstance(c, dcc.Graph)]


def test_word_counts_ignores_case_punctuation_and_blanks():
    assert word_counts(["Great!", "great idea", "", "  "]) == [("great", 2), ("idea", 1)]


def test_yesno_chart_includes_zero_counts():
    fig = question_chart(YESNO_Q, [_response(1, {"q_yn": "Yes"}), _response(2, {"q_yn": "Yes"})])
    assert list(fig.data[0].x) == ["Yes", "No"]
    assert list(fig.data[0].y) == [2, 0]


def test_checkbox_chart_counts_each_option_in_order():
    fig = question_chart(CHECKBOX_Q, [
        _response(1, {"q_cb": ["Red"]}), _response(2, {"q_cb": ["Red", "Green"]}), _response(3, {}),
    ])
    assert list(fig.data[0].x) == ["Red", "Blue", "Green"]
    assert list(fig.data[0].y) == [2, 0, 1]


def test_text_chart_with_no_words_has_no_bars():
    fig = question_chart(TEXT_Q, [_response(1, {"q_yn": "Yes"})])
    assert fig.layout.title.text == "Comments?"
    assert not fig.data or len(fig.data[0].x or ()) == 0


def test_response_table_rows_and_blank_cells():
    table = response_table(SURVEY, [
        _response(1, {"q_yn": "Yes", "q_cb": ["Red", "Green"]}), _response(2, {"q_text": "ok"}),
    ])
    assert [c["name"] for c in table.columns] == ["Respondent ID", "Submitted", "Comments?", "Attended?", "Colors?"]
    assert len(table.data) == 2
    assert table.data[0]["q_text"] == ""
    assert table.data[0]["q_cb"] == "Red, Green"


def test_build_results_without_responses_says_so():
    results = build_results(SURVEY, [])
    assert "Responses: 0" in str(results)
    assert "No responses yet" in str(results)
    assert _graphs(results) == []


def test_analyze_survey_end_to_end_through_storage(tmp_storage):
    save_survey(SURVEY)
    save_response(_response(1, {"q_yn": "No"}))
    results = analyze_survey("srv_demo")
    assert "Responses: 1" in str(results)
    assert len(_graphs(results)) == 3


def test_analyze_survey_missing_file_and_no_selection(tmp_storage):
    assert analyze_survey(None) == []
    assert "no longer exists" in str(analyze_survey("srv_gone"))


def test_word_counts_strips_quotes_and_keeps_accented_words():
    assert word_counts(["'Great' course", "great!", "students' don't", "café niño", "'"]) == [
        ("great", 2), ("café", 1), ("course", 1), ("don't", 1), ("niño", 1), ("students", 1),
    ]


def test_text_chart_ignores_answers_that_are_not_text():
    # e.g. a question changed from checkbox to text by editing the survey file
    fig = question_chart(TEXT_Q, [_response(1, {"q_text": ["Red"]}), _response(2, {"q_text": "fine"})])
    assert list(fig.data[0].x) == ["fine"]

import pytest

import src.constants as cn
from src.app import save_survey_callback
from src.storage import list_surveys, load_survey
from src.survey_maker import maker_layout


def _ids(component, id_type):
    return [c.id for c in component._traverse() if isinstance(getattr(c, "id", None), dict)
            and c.id.get("type") == id_type]


def _rows(*rows):
    """rows: (type, text, options) tuples; padded with blank rows to N_QUESTION_ROWS."""
    rows = list(rows) + [("text", "", "")] * (cn.N_QUESTION_ROWS - len(rows))
    return [r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows]


def test_maker_layout_has_n_rows_with_pattern_ids():
    layout = maker_layout()
    assert [i["row"] for i in _ids(layout, cn.MAKER_Q_TEXT)] == [0, 1, 2, 3, 4]
    assert len(_ids(layout, cn.MAKER_Q_TYPE)) == cn.N_QUESTION_ROWS
    assert len(_ids(layout, cn.MAKER_Q_OPTIONS)) == cn.N_QUESTION_ROWS


def test_save_creates_survey_with_questions_in_row_order(tmp_storage):
    status = save_survey_callback(1, "Demo", "", *_rows(
        ("text", "Name?", ""), ("text", "", ""), ("checkbox", "Colors?", "Red\nBlue"),
    ))
    assert "✅" in str(status) and "Demo" in str(status)
    [entry] = list_surveys()
    survey = load_survey(entry["id"])
    assert [(q.type, q.text, q.options) for q in survey.questions] == [
        ("text", "Name?", []), ("checkbox", "Colors?", ["Red", "Blue"]),
    ]


@pytest.mark.parametrize("title", ["", "   ", None])
def test_save_rejects_blank_and_whitespace_title(tmp_storage, title):
    status = save_survey_callback(1, title, "", *_rows(("text", "Name?", "")))
    assert "Please enter a survey title" in str(status)
    assert list_surveys() == []


def test_save_reports_row_errors_and_saves_nothing(tmp_storage):
    status = save_survey_callback(1, "Demo", "", *_rows(
        ("text", "Name?", ""), ("text", "", ""), ("checkbox", "Pick", "Only one"),
    ))
    assert "Question 3: a checkbox question needs at least 2 options." in str(status)
    assert list_surveys() == []


def test_save_twice_creates_two_surveys_with_same_title(tmp_storage):
    rows = _rows(("yesno", "Attended?", ""))
    save_survey_callback(1, "Demo", "", *rows)
    save_survey_callback(2, "Demo", "", *rows)
    surveys = list_surveys()
    assert [s["title"] for s in surveys] == ["Demo", "Demo"]
    assert surveys[0]["id"] != surveys[1]["id"]

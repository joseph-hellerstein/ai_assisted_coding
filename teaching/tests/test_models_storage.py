from src.models import Question, Response, Survey, generate_id
from src.storage import list_surveys, load_responses, load_survey, save_response, save_survey


def _survey(title="Demo"):
    return Survey(
        id=generate_id("srv_"),
        title=title,
        description="d",
        questions=[Question(id="q1", type="checkbox", text="Colors?", options=["A", "B"])],
    )


def _response(survey_id, submitted_at):
    return Response(
        id=generate_id("resp_"), survey_id=survey_id, submitted_at=submitted_at,
        respondent_id="12345", answers={"q1": ["A"]},
    )


def test_survey_round_trips_through_dict():
    s = _survey()
    assert Survey.from_dict(s.to_dict()) == s


def test_response_round_trips_through_dict():
    r = _response("srv_1", "2026-01-01T00:00:00")
    assert Response.from_dict(r.to_dict()) == r


def test_generate_id_has_prefix_and_is_unique():
    ids = [generate_id("resp_") for _ in range(100)]
    assert len(set(ids)) == 100
    assert all(i.startswith("resp_") for i in ids)


def test_save_and_load_survey(tmp_storage):
    s = _survey()
    save_survey(s)
    assert load_survey(s.id) == s
    assert (tmp_storage / "surveys" / f"{s.id}.json").exists()


def test_load_missing_survey_returns_none(tmp_storage):
    assert load_survey("nope") is None


def test_list_surveys_sorted_by_title_and_keeps_duplicate_titles(tmp_storage):
    for title in ["b", "A", "b"]:
        save_survey(_survey(title))
    assert [s["title"] for s in list_surveys()] == ["A", "b", "b"]


def test_load_responses_sorted_and_empty_when_none(tmp_storage):
    assert load_responses("srv_x") == []
    save_response(_response("srv_x", "2026-01-02T00:00:00"))
    save_response(_response("srv_x", "2026-01-01T00:00:00"))
    assert [r.submitted_at for r in load_responses("srv_x")] == [
        "2026-01-01T00:00:00", "2026-01-02T00:00:00",
    ]


def test_list_surveys_skips_unreadable_files(tmp_storage):
    good = _survey("Good")
    save_survey(good)
    (tmp_storage / "surveys" / "half_written.json").write_text('{"id": "srv_bad", "title":')
    (tmp_storage / "surveys" / "no_title.json").write_text('{"id": "srv_x"}')
    assert list_surveys() == [{"id": good.id, "title": "Good"}]


def test_load_survey_with_unreadable_file_returns_none(tmp_storage):
    (tmp_storage / "surveys").mkdir()
    (tmp_storage / "surveys" / "srv_bad.json").write_text("{ not json")
    assert load_survey("srv_bad") is None


def test_load_survey_ignores_unknown_keys_added_by_hand(tmp_storage):
    (tmp_storage / "surveys").mkdir()
    (tmp_storage / "surveys" / "srv_x.json").write_text(
        '{"id": "srv_x", "title": "T", "questions": '
        '[{"id": "q", "type": "text", "text": "Why?", "required": true}]}')
    assert load_survey("srv_x").questions == [Question(id="q", type="text", text="Why?")]


def test_load_responses_skips_unreadable_files(tmp_storage):
    save_response(_response("srv_x", "2026-01-01T00:00:00"))
    (tmp_storage / "responses" / "srv_x" / "broken.json").write_text("{")
    assert len(load_responses("srv_x")) == 1

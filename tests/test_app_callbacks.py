"""Tests for the Survey Maker / Taker callback functions in src/app.py.

These call the callback functions directly (Dash's @callback decorator
returns the plain function), bypassing the Dash server/dispatch layer, so
the data-assembly logic can be verified without a running app. Behavior
that genuinely depends on dash.callback_context (which trigger fired) is
covered instead by the Playwright acceptance test, since callback_context
is empty outside of a real request.
"""

import app as app_module


def test_save_survey_callback_captures_live_text_typed_into_the_form():
    # Regression test for the originally reported bug: the value the user
    # actually typed into the question text field must end up saved,
    # keyed by the question's stable id — not a stale placeholder.
    captured = {}
    app_module.save_survey = lambda survey: captured.__setitem__("survey", survey)
    app_module.list_surveys = lambda: []
    app_module.load_survey = lambda sid: None

    status, options = app_module.save_survey_callback(
        1, "My Survey", "A description", None,
        ["text"], [{"type": "q-type", "qid": "q_1"}],
        ["What is your name?"], [["req"]], [""],
        [1], [5], [""], [""], [""], [""],
    )

    saved = captured["survey"]
    assert saved.title == "My Survey"
    assert len(saved.questions) == 1
    assert saved.questions[0].id == "q_1"
    assert saved.questions[0].text == "What is your name?"


def test_save_survey_callback_parses_checkbox_options_from_textarea():
    captured = {}
    app_module.save_survey = lambda survey: captured.__setitem__("survey", survey)
    app_module.list_surveys = lambda: []
    app_module.load_survey = lambda sid: None

    app_module.save_survey_callback(
        1, "Colors", "", None,
        ["checkbox"], [{"type": "q-type", "qid": "q_2"}],
        ["Pick colors"], [[]], ["Red\nGreen\nBlue"],
        [1], [5], [""], [""], [""], [""],
    )

    saved_q = captured["survey"].questions[0]
    assert saved_q.options == ["Red", "Green", "Blue"]
    assert saved_q.required is False


def test_save_survey_callback_reuses_existing_survey_id_when_editing():
    captured = {}
    app_module.save_survey = lambda survey: captured.__setitem__("survey", survey)
    app_module.list_surveys = lambda: []
    app_module.load_survey = lambda sid: object() if sid == "srv_existing" else None

    app_module.save_survey_callback(
        1, "Edited title", "", "srv_existing",
        ["text"], [{"type": "q-type", "qid": "q_1"}],
        ["Q"], [["req"]], [""],
        [1], [5], [""], [""], [""], [""],
    )

    assert captured["survey"].id == "srv_existing"


def test_save_survey_callback_requires_a_title():
    status, options = app_module.save_survey_callback(
        1, "", "", None, [], [], [], [], [], [], [], [], [], [], [],
    )
    assert "title" in str(status).lower() or "⚠" in str(status)


def test_add_question_appends_to_existing_children_without_touching_them():
    existing = [{"type": "Div", "props": {"id": {"type": "q-wrapper", "qid": "q_1"}, "children": "kept as-is"}}]

    result = app_module.add_question(1, existing)

    assert len(result) == 2
    assert result[0] is existing[0]
    new_editor = result[1]
    assert new_editor.id["type"] == "q-wrapper"
    assert new_editor.id["qid"] != "q_1"


def test_add_question_on_empty_container_creates_one_question():
    result = app_module.add_question(1, None)
    assert len(result) == 1


def test_toggle_type_fields_shows_options_section_for_checkbox():
    options_style, scale_style, matrix_style = app_module.toggle_type_fields("checkbox")
    assert options_style["display"] == "block"
    assert scale_style["display"] == "none"
    assert matrix_style["display"] == "none"


def test_toggle_type_fields_shows_scale_section_for_likert():
    options_style, scale_style, matrix_style = app_module.toggle_type_fields("likert")
    assert options_style["display"] == "none"
    assert scale_style["display"] == "block"
    assert matrix_style["display"] == "none"


def test_toggle_type_fields_shows_matrix_section_for_matrix():
    options_style, scale_style, matrix_style = app_module.toggle_type_fields("matrix")
    assert options_style["display"] == "none"
    assert scale_style["display"] == "none"
    assert matrix_style["display"] == "block"


def test_submit_survey_response_saves_answers_keyed_by_question_id():
    captured = {}
    app_module.save_response = lambda response: captured.__setitem__("response", response)

    status = app_module.submit_survey_response(
        1, "srv_1",
        ["Yes", "Great answer"],
        [{"type": "answer", "qid": "q_1"}, {"type": "answer", "qid": "q_2"}],
    )

    resp = captured["response"]
    assert resp.survey_id == "srv_1"
    assert resp.answers == {"q_1": "Yes", "q_2": "Great answer"}
    assert "recorded" in str(status).lower() or "✅" in str(status)


def test_submit_survey_response_splits_matrix_composite_answers():
    captured = {}
    app_module.save_response = lambda response: captured.__setitem__("response", response)

    app_module.submit_survey_response(
        1, "srv_1",
        ["Good"],
        [{"type": "answer", "qid": "q_9::Speed"}],
    )

    assert captured["response"].answers == {"q_9_matrix_Speed": "Good"}


def test_submit_survey_response_without_survey_selected_does_not_save():
    saved = []
    app_module.save_response = lambda response: saved.append(response)

    app_module.submit_survey_response(1, None, [], [])

    assert saved == []


def test_show_survey_only_renders_form_no_inline_callback_registration():
    # Regression guard for the dynamic-callback-registration bug: show_survey
    # must not define/register a *nested* @callback each time it runs (its
    # own top-level decorator is fine and expected).
    import inspect
    source = inspect.getsource(app_module.show_survey)
    # Strip the decorator block itself, keep only the function body.
    body = source[source.index("\ndef show_survey"):]
    assert "@callback" not in body
    assert "def submit_survey" not in body


def test_confirm_delete_survey_opens_dialog_with_survey_title_when_selected():
    app_module.load_survey = lambda sid: type("S", (), {"title": "My Survey"})()

    displayed, message, status = app_module.confirm_delete_survey(1, "srv_1")

    assert displayed is True
    assert "My Survey" in message


def test_confirm_delete_survey_shows_warning_when_none_selected():
    displayed, message, status = app_module.confirm_delete_survey(1, None)

    assert displayed is False
    assert "⚠" in str(status) or "select" in str(status).lower()


def test_perform_delete_survey_calls_storage_delete_with_correct_id():
    captured = {}
    app_module.delete_survey = lambda sid: captured.__setitem__("deleted_id", sid)
    app_module.list_surveys = lambda: []

    app_module.perform_delete_survey(1, "srv_to_remove")

    assert captured["deleted_id"] == "srv_to_remove"


def test_perform_delete_survey_resets_the_editor_form():
    app_module.delete_survey = lambda sid: None
    app_module.list_surveys = lambda: []

    status, options, title, description, questions, select_value = \
        app_module.perform_delete_survey(1, "srv_1")

    assert title == ""
    assert description == ""
    assert questions == []
    assert select_value is None


def test_perform_delete_survey_refreshes_dropdown_excluding_deleted_survey():
    app_module.delete_survey = lambda sid: None
    app_module.list_surveys = lambda: [{"title": "Remaining Survey", "id": "srv_2"}]

    status, options, title, description, questions, select_value = \
        app_module.perform_delete_survey(1, "srv_1")

    assert options == [{"label": "Remaining Survey", "value": "srv_2"}]
    assert "deleted" in str(status).lower() or "✅" in str(status)


def test_submit_callback_is_registered_statically_at_import_time():
    # The real bug-5 regression guard: the submit callback must be part of
    # the app's callback graph from the moment the module is imported, not
    # only after a survey has been selected once (which never actually
    # wired it to the frontend at all).
    from dash._callback import GLOBAL_CALLBACK_MAP
    keys = list(app_module.app.callback_map.keys()) + list(GLOBAL_CALLBACK_MAP.keys())
    assert any("taker-status" in k for k in keys)

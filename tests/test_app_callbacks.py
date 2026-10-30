"""Tests for the Survey Maker / Taker callback functions in src/app.py.

These call the callback functions directly (Dash's @callback decorator
returns the plain function), bypassing the Dash server/dispatch layer, so
the data-assembly logic can be verified without a running app. Behavior
that genuinely depends on dash.callback_context (which trigger fired) is
covered instead by the Playwright acceptance test, since callback_context
is empty outside of a real request.
"""

import app as app_module  # type: ignore
from typing import cast
from models import Question, Survey  # type: ignore


def test_save_survey_callback_captures_live_text_typed_into_the_form():
    # Regression test for the originally reported bug: the value the user
    # actually typed into the question text field must end up saved,
    # keyed by the question's stable id — not a stale placeholder.
    captured = {}
    app_module.save_survey = lambda survey: captured.__setitem__("survey", survey)
    app_module.list_surveys = lambda: []
    app_module.load_survey = lambda sid: None

    status, options, tab_label = app_module.save_survey_callback(
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
    status, options, tab_label = app_module.save_survey_callback(
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

    status, *_ = app_module.submit_survey_response(
        1, "srv_1",
        ["Yes", "Great answer"],
        [{"type": "answer", "qid": "q_1"}, {"type": "answer", "qid": "q_2"}],
        None, "12345",
    )

    resp = captured["response"]
    assert resp.survey_id == "srv_1"
    assert resp.answers == {"q_1": "Yes", "q_2": "Great answer"}
    assert resp.respondent_id == "12345"
    assert "recorded" in str(status).lower() or "✅" in str(status)


def test_submit_survey_response_splits_matrix_composite_answers():
    captured = {}
    app_module.save_response = lambda response: captured.__setitem__("response", response)

    app_module.submit_survey_response(
        1, "srv_1",
        ["Good"],
        [{"type": "answer", "qid": "q_9::Speed"}],
        None, "12345",
    )

    assert captured["response"].answers == {"q_9_matrix_Speed": "Good"}


def test_submit_survey_response_without_survey_selected_does_not_save():
    saved = []
    app_module.save_response = lambda response: saved.append(response)

    app_module.submit_survey_response(1, None, [], [], None, "12345")

    assert saved == []


def test_submit_survey_response_rejects_an_invalid_respondent_id():
    saved = []
    app_module.save_response = lambda response: saved.append(response)

    status, *_ = app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], None, "12ab",
    )

    assert saved == []
    assert "5 digits" in str(status) or "⚠" in str(status)


def test_submit_survey_response_deletes_the_resumed_draft_after_saving():
    app_module.save_response = lambda response: None
    deleted = {}
    app_module.delete_draft = lambda survey_id, draft_id: deleted.update(
        survey_id=survey_id, draft_id=draft_id
    )
    app_module.list_drafts = lambda survey_id: []
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])
    app_module.list_surveys = lambda: []
    app_module.load_responses = lambda sid: []

    status, current_draft_id, section_style, taker_label, analyzer_label = app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1", "12345",
    )

    assert deleted == {"survey_id": "srv_1", "draft_id": "draft_1"}
    assert current_draft_id is None
    # That was the only draft, and it's gone now: section hides.
    assert section_style.get("display") == "none"


def test_submit_survey_response_keeps_the_section_visible_if_other_drafts_remain():
    app_module.save_response = lambda response: None
    app_module.delete_draft = lambda survey_id, draft_id: None
    app_module.list_drafts = lambda survey_id: [
        {"id": "draft_other", "label": "", "saved_at": "2026-10-20T09:00:00"}
    ]
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])
    app_module.list_surveys = lambda: []
    app_module.load_responses = lambda sid: []

    status, current_draft_id, section_style, taker_label, analyzer_label = app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1", "12345",
    )

    assert section_style.get("display") == "block"


def test_submit_survey_response_without_a_resumed_draft_does_not_touch_drafts():
    app_module.save_response = lambda response: None
    app_module.delete_draft = lambda survey_id, draft_id: (_ for _ in ()).throw(
        AssertionError("delete_draft should not be called when nothing was resumed")
    )

    app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], None, "12345",
    )


def test_submit_survey_response_ignores_the_spurious_zero_click_mount_event():
    # Regression guard: the Submit button is recreated by show_survey every
    # time a survey/draft is selected, and Dash fires a callback like this
    # one once, spuriously, at n_clicks=0 the moment that freshly-mounted
    # button first appears, whenever the callback also writes to a
    # component that already exists outside the dynamic form (here, the
    # draft-id Store) -- it must do nothing, not save a phantom response.
    saved = []
    app_module.save_response = lambda response: saved.append(response)

    status, current_draft_id, section_style, taker_label, analyzer_label = app_module.submit_survey_response(
        0, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1", "12345",
    )

    assert saved == []
    assert status is app_module.no_update
    assert current_draft_id is app_module.no_update
    assert section_style is app_module.no_update
    assert taker_label is app_module.no_update
    assert analyzer_label is app_module.no_update


def test_taker_tab_label_lists_drafts_for_every_survey():
    # Regression guard for the actual bug report: generating/saving a
    # draft for ANY survey must show up here, not just whichever survey
    # happens to be selected in the Taker's own dropdown right now.
    app_module.list_surveys = lambda: [
        {"id": "srv_1", "title": "Alpha"},
        {"id": "srv_2", "title": "Beta"},
    ]
    app_module.get_draft_info = lambda sid: (
        {"srv_1": ("Alpha", 2, 5, 1), "srv_2": ("", 0, 0, 0)}[sid]
    )

    label = app_module._taker_tab_label()

    assert "Alpha" in label and "2/5 answered" in label
    assert "Beta" in label and "no drafts" in label


def test_taker_tab_label_mentions_how_many_drafts_a_survey_has():
    app_module.list_surveys = lambda: [{"id": "srv_1", "title": "Alpha"}]
    app_module.get_draft_info = lambda sid: ("Alpha", 2, 5, 3)

    label = app_module._taker_tab_label()

    assert "3 drafts" in label


def test_taker_tab_label_shows_placeholder_when_no_surveys_exist():
    app_module.list_surveys = lambda: []

    label = app_module._taker_tab_label()

    assert "No surveys yet" in label


def test_refresh_taker_tab_hover_reflects_every_survey():
    app_module.list_surveys = lambda: [{"id": "srv_1", "title": "Fresh Survey"}]
    app_module.get_draft_info = lambda sid: ("", 0, 0, 0)

    label = app_module.refresh_taker_tab_hover("tab-taker")

    assert "Fresh Survey" in label


def test_analyzer_tab_label_lists_response_counts_for_every_survey():
    app_module.list_surveys = lambda: [
        {"id": "srv_1", "title": "Alpha"},
        {"id": "srv_2", "title": "Beta"},
    ]
    app_module.load_responses = lambda sid: ({"srv_1": [1, 2, 3], "srv_2": []}[sid])

    label = app_module._analyzer_tab_label()

    assert "Alpha" in label and "3 responses" in label
    assert "Beta" in label and "0 responses" in label


def test_analyzer_tab_label_shows_placeholder_when_no_surveys_exist():
    app_module.list_surveys = lambda: []

    label = app_module._analyzer_tab_label()

    assert "No surveys yet" in label


def test_refresh_analyzer_tab_hover_reflects_every_survey():
    app_module.list_surveys = lambda: [{"id": "srv_1", "title": "Fresh Survey"}]
    app_module.load_responses = lambda sid: []

    label = app_module.refresh_analyzer_tab_hover("tab-analyzer")

    assert "Fresh Survey" in label


def test_refresh_draft_list_hides_the_section_when_the_survey_has_no_drafts():
    app_module.list_drafts = lambda survey_id: []

    options, style = app_module.refresh_draft_list("srv_1")

    assert options == []
    assert style.get("display") == "none"


def test_refresh_draft_list_shows_the_section_when_the_survey_has_drafts():
    app_module.list_drafts = lambda survey_id: [
        {"id": "draft_1", "label": "My draft", "saved_at": "2026-10-20T09:00:00"}
    ]

    options, style = app_module.refresh_draft_list("srv_1")

    assert len(options) == 1
    assert style.get("display") == "block"


def test_refresh_draft_list_hides_the_section_when_no_survey_selected():
    options, style = app_module.refresh_draft_list(None)

    assert options == []
    assert style.get("display") == "none"


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
    assert ("My Survey" in cast(str, message))


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

    status, options, title, description, questions, select_value, editor_style, maker_label, taker_label, analyzer_label = \
        app_module.perform_delete_survey(1, "srv_1")

    assert title == ""
    assert description == ""
    assert questions == []
    assert select_value is None
    assert editor_style.get("display") == "none"


def test_perform_delete_survey_refreshes_dropdown_excluding_deleted_survey():
    app_module.delete_survey = lambda sid: None
    app_module.list_surveys = lambda: [{"title": "Remaining Survey", "id": "srv_2"}]
    app_module.get_draft_info = lambda sid: ("", 0, 0, 0)
    app_module.load_responses = lambda sid: []

    status, options, title, description, questions, select_value, editor_style, maker_label, taker_label, analyzer_label = \
        app_module.perform_delete_survey(1, "srv_1")

    assert options == [{"label": "Remaining Survey", "value": "srv_2"}]
    assert "deleted" in str(status).lower() or "✅" in str(status)


def test_save_draft_callback_saves_live_answers_and_generates_a_new_draft_id():
    captured = {}
    app_module.save_draft = lambda draft: captured.__setitem__("draft", draft)
    app_module.list_drafts = lambda survey_id: []
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])

    status, options, select_value, current_draft_id, section_style, tab_label = app_module.save_draft_callback(
        1, "srv_1", "My label", None,
        ["Yes"], [{"type": "answer", "qid": "q_1"}], "12345",
    )

    draft = captured["draft"]
    assert draft.survey_id == "srv_1"
    assert draft.label == "My label"
    assert draft.answers == {"q_1": "Yes"}
    assert draft.respondent_id == "12345"
    # select_value is deliberately left as no_update: writing it would be an
    # Input to show_survey, which would immediately rebuild the form and
    # wipe this very status message.
    assert select_value is app_module.no_update
    # current_draft_id is deliberately left as no_update too (it was None
    # going in, i.e. nothing was explicitly resumed): tracking this fresh
    # draft as "current" would make the *next* unrelated Save for Later
    # click silently overwrite it instead of creating its own new draft.
    assert current_draft_id is app_module.no_update
    assert "✅" in str(status) or "saved" in str(status).lower()


def test_save_draft_callback_creates_a_separate_draft_each_time_nothing_was_resumed():
    # Regression guard: two distinct, never-resumed save attempts (e.g. the
    # user fills in a survey, saves, keeps editing, and saves again without
    # ever picking anything from the resume dropdown) must end up as two
    # separate drafts, not one overwriting the other.
    saved_ids = []
    app_module.save_draft = lambda draft: saved_ids.append(draft.id)
    app_module.list_drafts = lambda survey_id: []

    app_module.save_draft_callback(1, "srv_1", "", None, ["Yes"], [{"type": "answer", "qid": "q_1"}], "12345")
    app_module.save_draft_callback(1, "srv_1", "", None, ["No"], [{"type": "answer", "qid": "q_1"}], "12345")

    assert len(saved_ids) == 2
    assert saved_ids[0] != saved_ids[1]


def test_save_draft_callback_reuses_the_current_draft_id_instead_of_duplicating():
    captured = {}
    app_module.save_draft = lambda draft: captured.__setitem__("draft", draft)
    app_module.list_drafts = lambda survey_id: []

    app_module.save_draft_callback(
        1, "srv_1", "", "draft_existing",
        ["Yes"], [{"type": "answer", "qid": "q_1"}], "12345",
    )

    assert captured["draft"].id == "draft_existing"


def test_save_draft_callback_without_survey_selected_shows_warning_and_does_not_save():
    saved = []
    app_module.save_draft = lambda draft: saved.append(draft)

    status, options, select_value, current_draft_id, section_style, tab_label = app_module.save_draft_callback(
        1, None, "", None, [], [], "12345",
    )

    assert saved == []
    assert "⚠" in str(status) or "select" in str(status).lower()


def test_take_another_survey_clears_the_survey_dropdown_and_hides_the_thank_you_screen():
    # The thank-you screen used to be a dead end: clearing the dropdown is
    # what actually resets everything downstream, since it's show_survey's
    # own Input.
    select_value, form_style, thankyou_style = app_module.take_another_survey(1)

    assert select_value is None
    assert thankyou_style.get("display") == "none"


def test_take_another_survey_ignores_the_spurious_zero_click_mount_event():
    select_value, form_style, thankyou_style = app_module.take_another_survey(0)

    assert select_value is app_module.no_update
    assert form_style is app_module.no_update
    assert thankyou_style is app_module.no_update


def test_submit_callback_is_registered_statically_at_import_time():
    # The real bug-5 regression guard: the submit callback must be part of
    # the app's callback graph from the moment the module is imported, not
    # only after a survey has been selected once (which never actually
    # wired it to the frontend at all).
    from dash._callback import GLOBAL_CALLBACK_MAP
    keys = list(app_module.app.callback_map.keys()) + list(GLOBAL_CALLBACK_MAP.keys())
    assert any("taker-status" in k for k in keys)


def test_delete_draft_callback_deletes_the_current_draft_and_clears_store():
    deleted = {}
    app_module.delete_draft = lambda survey_id, draft_id: deleted.update(
        survey_id=survey_id, draft_id=draft_id
    )
    app_module.list_drafts = lambda survey_id: [
        {"id": "draft_other", "label": "", "saved_at": "2026-10-20T09:00:00"}
    ]
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])

    status, form, current_draft_id, section_style, tab_label = app_module.delete_draft_callback(
        1, "srv_1", "draft_1",
    )

    assert deleted == {"survey_id": "srv_1", "draft_id": "draft_1"}
    assert current_draft_id is None
    # The status message is baked into the rebuilt form itself (see the
    # dedicated test below for why), so this Output is a no-op here.
    assert status is app_module.no_update
    [form_component] = form
    status_div = _find_answer_component(form_component, "taker-status")
    assert "deleted" in str(status_div.children).lower()
    # Another draft still exists for this survey, so the section stays visible.
    assert section_style.get("display") == "block"


def test_delete_draft_callback_resets_the_form_to_blank_no_answers_filled_in():
    # The user should land back on a blank Survey Taker, not on the
    # resumed draft's answers, once that draft no longer exists.
    deleted = {}
    app_module.delete_draft = lambda survey_id, draft_id: deleted.update(
        survey_id=survey_id, draft_id=draft_id
    )
    app_module.list_drafts = lambda survey_id: []
    q = Question(id="q_1", type="text", text="Tell us more")
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[q])

    status, form, current_draft_id, section_style, tab_label = app_module.delete_draft_callback(
        1, "srv_1", "draft_1",
    )

    [form_component] = form
    answer_field = _find_answer_component(form_component, {"type": "answer", "qid": "q_1"})
    assert answer_field is not None
    assert answer_field.value == ""


def _find_answer_component(component, target_id):
    cid = getattr(component, "id", None)
    if cid == target_id:
        return component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for c in children:
            found = _find_answer_component(c, target_id)
            if found is not None:
                return found
    elif children is not None and (hasattr(children, "id") or hasattr(children, "children")):
        return _find_answer_component(children, target_id)
    return None


def test_delete_draft_callback_hides_section_when_no_drafts_remain():
    app_module.delete_draft = lambda survey_id, draft_id: None
    app_module.list_drafts = lambda survey_id: []
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])

    status, form, current_draft_id, section_style, tab_label = app_module.delete_draft_callback(
        1, "srv_1", "draft_1",
    )

    assert section_style.get("display") == "none"


def test_delete_draft_callback_without_a_draft_selected_shows_warning():
    app_module.delete_draft = lambda survey_id, draft_id: (_ for _ in ()).throw(
        AssertionError("delete_draft should not be called when nothing is selected")
    )

    status, form, current_draft_id, section_style, tab_label = app_module.delete_draft_callback(
        1, "srv_1", None,
    )

    assert "⚠" in str(status) or "no draft" in str(status).lower()
    assert form is app_module.no_update


def test_delete_response_row_persists_deletion_and_refreshes_summary():
    deleted = {}
    app_module.delete_response = lambda response_id, survey_id: deleted.update(
        response_id=response_id, survey_id=survey_id
    )
    app_module.load_survey = lambda sid: type(
        "S", (), {"title": "My Survey", "questions": []}
    )()
    app_module.load_responses = lambda sid: []
    app_module.list_surveys = lambda: []

    data_previous = [
        {"Response ID": "resp_1", "Submitted At": "t1"},
        {"Response ID": "resp_2", "Submitted At": "t2"},
    ]
    data = [{"Response ID": "resp_1", "Submitted At": "t1"}]

    response_count, charts, analyzer_label = app_module.delete_response_row(data, data_previous, "srv_1")

    assert deleted == {"response_id": "resp_2", "survey_id": "srv_1"}
    assert "My Survey" in str(response_count)


def test_delete_response_row_ignores_a_survey_switch_data_change():
    # Switching surveys also rewrites the table's "data" via analyze_survey.
    # None of the new survey's response ids were present before, so this
    # must NOT be misread as "every old response got deleted".
    called = []
    app_module.delete_response = lambda response_id, survey_id: called.append(response_id)

    data_previous = [{"Response ID": "resp_1", "Submitted At": "t1"}]
    data = [{"Response ID": "resp_other", "Submitted At": "t9"}]

    app_module.delete_response_row(data, data_previous, "srv_2")

    assert called == []


def test_delete_response_row_ignores_changes_that_are_not_a_single_row_removal():
    called = []
    app_module.delete_response = lambda response_id, survey_id: called.append(response_id)

    data_previous = [{"Response ID": "resp_1", "Submitted At": "t1"}]
    data = [
        {"Response ID": "resp_1", "Submitted At": "t1"},
        {"Response ID": "resp_2", "Submitted At": "t2"},
    ]

    app_module.delete_response_row(data, data_previous, "srv_1")

    assert called == []


def test_toggle_test_panel_opens_when_currently_hidden():
    style = app_module.toggle_test_panel(1, {"display": "none"})

    assert style["display"] == "block"


def test_toggle_test_panel_closes_when_currently_open():
    style = app_module.toggle_test_panel(1, {"display": "block"})

    assert style["display"] == "none"


def test_generate_test_data_creates_a_survey_and_the_requested_responses():
    captured = {}
    app_module.sample_data.save_survey = lambda survey: captured.__setitem__("survey", survey)
    saved_responses = []
    saved_drafts = []
    app_module.sample_data.save_response = lambda r: saved_responses.append(r)
    app_module.sample_data.save_draft = lambda d: saved_drafts.append(d)
    app_module.list_surveys = lambda: []

    status, maker_label, taker_label, analyzer_label = app_module.generate_test_data(1, 3, 2)

    assert len(saved_responses) == 3
    assert len(saved_drafts) == 2
    assert "✅" in str(status)


def test_generate_test_data_rejects_negative_counts():
    status = app_module.generate_test_data(1, -1, 0)

    assert "⚠" in str(status)


def test_generate_test_data_rejects_non_numeric_counts():
    status = app_module.generate_test_data(1, "abc", 0)

    assert "⚠" in str(status)


def test_delete_all_test_data_reports_how_many_surveys_were_removed():
    app_module.sample_data.list_surveys = lambda: [
        {"id": "srv_rand_1", "title": "Random 1"},
        {"id": "srv_real_1", "title": "Real survey"},
    ]
    app_module.sample_data.list_drafts = lambda sid: []
    app_module.sample_data.delete_survey = lambda sid: None
    app_module.list_surveys = lambda: []

    status, maker_label, taker_label, analyzer_label = app_module.delete_all_test_data(1)

    assert "1" in str(status)


def test_maker_tab_label_lists_every_saved_survey():
    app_module.list_surveys = lambda: [{"title": "Alpha"}, {"title": "Beta"}]

    label = app_module._maker_tab_label()

    assert "Alpha" in label
    assert "Beta" in label


def test_maker_tab_label_shows_placeholder_when_no_surveys_exist():
    app_module.list_surveys = lambda: []

    label = app_module._maker_tab_label()

    assert "No surveys yet" in label


def test_refresh_maker_tab_hover_reflects_current_survey_list():
    app_module.list_surveys = lambda: [{"title": "Fresh Survey"}]

    label = app_module.refresh_maker_tab_hover("tab-maker")

    assert "Fresh Survey" in label


def test_generate_test_data_refreshes_all_three_tab_hovers():
    app_module.sample_data.save_survey = lambda survey: None
    app_module.sample_data.save_response = lambda r: None
    app_module.sample_data.save_draft = lambda d: None
    app_module.list_surveys = lambda: [{"title": "Newly Generated", "id": "srv_1"}]
    app_module.get_draft_info = lambda sid: ("", 0, 0, 0)
    app_module.load_responses = lambda sid: []

    status, maker_label, taker_label, analyzer_label = app_module.generate_test_data(1, 0, 0)

    assert "Newly Generated" in maker_label
    assert "Newly Generated" in taker_label
    assert "Newly Generated" in analyzer_label


def test_delete_all_test_data_refreshes_all_three_tab_hovers():
    app_module.sample_data.list_surveys = lambda: []
    app_module.sample_data.list_drafts = lambda sid: []
    app_module.sample_data.delete_survey = lambda sid: None
    app_module.list_surveys = lambda: [{"title": "Still Here", "id": "srv_2"}]
    app_module.get_draft_info = lambda sid: ("", 0, 0, 0)
    app_module.load_responses = lambda sid: []

    status, maker_label, taker_label, analyzer_label = app_module.delete_all_test_data(1)

    assert "Still Here" in maker_label
    assert "Still Here" in taker_label
    assert "Still Here" in analyzer_label


def test_render_active_tab_highlights_the_active_button_and_shows_its_content():
    maker_style, taker_style, analyzer_style, maker_content, taker_content, analyzer_content = \
        app_module.render_active_tab(app_module.TAB_TAKER)

    assert taker_style["borderBottom"] != "3px solid transparent"
    assert maker_style["borderBottom"] == "3px solid transparent"
    assert analyzer_style["borderBottom"] == "3px solid transparent"

    assert taker_content["display"] == "block"
    assert maker_content["display"] == "none"
    assert analyzer_content["display"] == "none"


def test_render_active_tab_shows_nothing_when_collapsed():
    _, _, _, maker_content, taker_content, analyzer_content = app_module.render_active_tab(None)

    assert maker_content["display"] == "none"
    assert taker_content["display"] == "none"
    assert analyzer_content["display"] == "none"


# toggle_active_tab itself isn't direct-call-tested here: it reads
# dash.callback_context.triggered to tell which button fired, and that's
# only available inside a real Dash request (calling it directly raises
# MissingCallbackContextException) -- same situation as show_survey
# elsewhere in this file. Its click-driven toggle/collapse behavior is
# covered by the Playwright acceptance check instead.

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

    status, *_ = app_module.submit_survey_response(
        1, "srv_1",
        ["Yes", "Great answer"],
        [{"type": "answer", "qid": "q_1"}, {"type": "answer", "qid": "q_2"}],
        None,
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
        None,
    )

    assert captured["response"].answers == {"q_9_matrix_Speed": "Good"}


def test_submit_survey_response_without_survey_selected_does_not_save():
    saved = []
    app_module.save_response = lambda response: saved.append(response)

    app_module.submit_survey_response(1, None, [], [], None)

    assert saved == []


def test_submit_survey_response_deletes_the_resumed_draft_after_saving():
    app_module.save_response = lambda response: None
    deleted = {}
    app_module.delete_draft = lambda survey_id, draft_id: deleted.update(
        survey_id=survey_id, draft_id=draft_id
    )
    app_module.list_drafts = lambda survey_id: []
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])

    status, current_draft_id, section_style, tab_label = app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1",
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

    status, current_draft_id, section_style, tab_label = app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1",
    )

    assert section_style.get("display") == "block"


def test_submit_survey_response_without_a_resumed_draft_does_not_touch_drafts():
    app_module.save_response = lambda response: None
    app_module.delete_draft = lambda survey_id, draft_id: (_ for _ in ()).throw(
        AssertionError("delete_draft should not be called when nothing was resumed")
    )

    app_module.submit_survey_response(
        1, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], None,
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

    status, current_draft_id, section_style, tab_label = app_module.submit_survey_response(
        0, "srv_1", ["Yes"], [{"type": "answer", "qid": "q_1"}], "draft_1",
    )

    assert saved == []
    assert status is app_module.no_update
    assert current_draft_id is app_module.no_update
    assert section_style is app_module.no_update
    assert tab_label is app_module.no_update


def test_taker_tab_label_shows_no_current_draft_when_nothing_qualifies():
    app_module.get_draft_info = lambda survey_id: ("", 0, 0, 0)

    label = app_module._taker_tab_label(None)

    assert label.title == "No current draft"


def test_taker_tab_label_shows_progress_for_the_selected_surveys_draft():
    app_module.get_draft_info = lambda survey_id: ("My Survey", 2, 5, 1)

    label = app_module._taker_tab_label("srv_1")

    assert label.title == "My Survey: 2/5 answered"


def test_taker_tab_label_mentions_extra_drafts_when_more_than_one_exists():
    app_module.get_draft_info = lambda survey_id: ("My Survey", 2, 5, 3)

    label = app_module._taker_tab_label("srv_1")

    assert "3 drafts saved" in label.title


def test_refresh_taker_tab_hover_delegates_to_the_currently_selected_survey():
    # Regression guard for the actual bug report: this must be keyed off
    # whichever survey is selected in the Taker's own dropdown right now,
    # not computed once when the server process started (which is why the
    # old version could show a draft that had since been deleted, or miss
    # one that had since been created).
    seen = []
    app_module.get_draft_info = lambda survey_id: seen.append(survey_id) or ("", 0, 0, 0)

    app_module.refresh_taker_tab_hover("tab-taker", "srv_42")

    assert seen == ["srv_42"]


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


def test_save_draft_callback_saves_live_answers_and_generates_a_new_draft_id():
    captured = {}
    app_module.save_draft = lambda draft: captured.__setitem__("draft", draft)
    app_module.list_drafts = lambda survey_id: []
    app_module.load_survey = lambda sid: Survey(id=sid, title="T", questions=[])

    status, options, select_value, current_draft_id, section_style, tab_label = app_module.save_draft_callback(
        1, "srv_1", "My label", None,
        ["Yes"], [{"type": "answer", "qid": "q_1"}],
    )

    draft = captured["draft"]
    assert draft.survey_id == "srv_1"
    assert draft.label == "My label"
    assert draft.answers == {"q_1": "Yes"}
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

    app_module.save_draft_callback(1, "srv_1", "", None, ["Yes"], [{"type": "answer", "qid": "q_1"}])
    app_module.save_draft_callback(1, "srv_1", "", None, ["No"], [{"type": "answer", "qid": "q_1"}])

    assert len(saved_ids) == 2
    assert saved_ids[0] != saved_ids[1]


def test_save_draft_callback_reuses_the_current_draft_id_instead_of_duplicating():
    captured = {}
    app_module.save_draft = lambda draft: captured.__setitem__("draft", draft)
    app_module.list_drafts = lambda survey_id: []

    app_module.save_draft_callback(
        1, "srv_1", "", "draft_existing",
        ["Yes"], [{"type": "answer", "qid": "q_1"}],
    )

    assert captured["draft"].id == "draft_existing"


def test_save_draft_callback_without_survey_selected_shows_warning_and_does_not_save():
    saved = []
    app_module.save_draft = lambda draft: saved.append(draft)

    status, options, select_value, current_draft_id, section_style, tab_label = app_module.save_draft_callback(
        1, None, "", None, [], [],
    )

    assert saved == []
    assert "⚠" in str(status) or "select" in str(status).lower()


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

    data_previous = [
        {"Response ID": "resp_1", "Submitted At": "t1"},
        {"Response ID": "resp_2", "Submitted At": "t2"},
    ]
    data = [{"Response ID": "resp_1", "Submitted At": "t1"}]

    response_count, charts = app_module.delete_response_row(data, data_previous, "srv_1")

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

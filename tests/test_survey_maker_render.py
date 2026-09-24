"""Tests for the Survey Maker question editor rendering (src/survey_maker.py).

Covers the completed pattern-matching-id refactor: every question editor is
keyed by a stable `qid` (not a positional index), type-specific sections are
always rendered (visibility toggled, never rebuilt), and options / matrix
rows / matrix columns are single "one item per line" textareas.
"""

from models import Question  # type: ignore
from survey_maker import render_question_editor, survey_maker_layout  # type: ignore


def _collect_by_id(component, out=None):
    """Recursively collect {id: component} for every id'd component in a Dash tree."""
    if out is None:
        out = {}
    cid = getattr(component, "id", None)
    if cid is not None:
        out[_id_key(cid)] = component
    children = getattr(component, "children", None)
    if children is None:
        pass
    elif isinstance(children, (list, tuple)):
        for c in children:
            if hasattr(c, "id") or hasattr(c, "children"):
                _collect_by_id(c, out)
    elif hasattr(children, "id") or hasattr(children, "children"):
        _collect_by_id(children, out)
    return out


def _id_key(cid):
    if isinstance(cid, dict):
        return (cid.get("type"), cid.get("qid"))
    return cid


def test_render_question_editor_uses_qid_not_index_in_ids():
    editor = render_question_editor(None, "q_abc123")
    ids = _collect_by_id(editor)
    assert ("q-text", "q_abc123") in ids
    assert ("q-type", "q_abc123") in ids
    assert ("q-wrapper", "q_abc123") in ids
    assert ("delete-q", "q_abc123") in ids


def test_render_question_editor_prefills_existing_question_values():
    q = Question(id="q_1", type="checkbox", text="Pick colors", required=False,
                 options=["Red", "Green", "Blue"])
    editor = render_question_editor(q, "q_1")
    ids = _collect_by_id(editor)

    assert ids[("q-text", "q_1")].value == "Pick colors"
    assert ids[("q-type", "q_1")].value == "checkbox"
    assert ids[("q-required", "q_1")].value == []
    assert ids[("q-options", "q_1")].value == "Red\nGreen\nBlue"


def test_render_question_editor_defaults_required_checked_for_new_question():
    editor = render_question_editor(None, "q_new")
    ids = _collect_by_id(editor)
    assert ids[("q-required", "q_new")].value == ["req"]


def test_render_question_editor_always_renders_all_type_sections():
    # Sections must always be present (never conditionally omitted) so that
    # ALL-pattern State lists across different question types stay aligned;
    # visibility is controlled via style, not presence.
    for qtype in ("text", "checkbox", "likert", "matrix", "yesno"):
        q = Question(id="q_x", type=qtype, text="")
        editor = render_question_editor(q, "q_x")
        ids = _collect_by_id(editor)
        assert ("q-options", "q_x") in ids, qtype
        assert ("q-scale-min", "q_x") in ids, qtype
        assert ("q-scale-max", "q_x") in ids, qtype
        assert ("q-scale-label-min", "q_x") in ids, qtype
        assert ("q-scale-label-max", "q_x") in ids, qtype
        assert ("q-matrix-rows", "q_x") in ids, qtype
        assert ("q-matrix-cols", "q_x") in ids, qtype


def test_render_question_editor_hides_non_matching_sections_via_style():
    q = Question(id="q_x", type="checkbox", text="")
    editor = render_question_editor(q, "q_x")
    ids = _collect_by_id(editor)

    options_wrap = ids[("q-options-wrap", "q_x")]
    scale_wrap = ids[("q-scale-wrap", "q_x")]
    matrix_wrap = ids[("q-matrix-wrap", "q_x")]

    assert options_wrap.style.get("display") != "none"
    assert scale_wrap.style.get("display") == "none"
    assert matrix_wrap.style.get("display") == "none"


def test_survey_maker_layout_has_a_delete_survey_button():
    layout = survey_maker_layout()
    ids = _collect_by_id(layout)
    assert "maker-delete-survey" in ids


def test_survey_maker_layout_has_a_confirm_dialog_for_deletion():
    layout = survey_maker_layout()
    ids = _collect_by_id(layout)
    assert "maker-delete-confirm" in ids
    dialog = ids["maker-delete-confirm"]
    assert type(dialog).__name__ == "ConfirmDialog"


def test_render_question_editor_matrix_rows_cols_prefilled_as_lines():
    q = Question(id="q_m", type="matrix", text="",
                 matrix_rows=["Speed", "Quality"], matrix_cols=["Poor", "Good"])
    editor = render_question_editor(q, "q_m")
    ids = _collect_by_id(editor)
    assert ids[("q-matrix-rows", "q_m")].value == "Speed\nQuality"
    assert ids[("q-matrix-cols", "q_m")].value == "Poor\nGood"

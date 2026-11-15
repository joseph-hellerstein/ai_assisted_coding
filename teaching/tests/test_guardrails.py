"""Checks that the teaching edition stays as small and simple as its spec says."""
import ast
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
CALLBACKS = {"save_survey_callback", "refresh_survey_lists", "show_survey",
             "submit_survey_response", "analyze_survey"}


def _callback_functions():
    tree = ast.parse((SRC / "app.py").read_text())
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
            and any(isinstance(d, ast.Call) and getattr(d.func, "id", None) == "callback"
                    for d in node.decorator_list)]


def test_exactly_five_callbacks():
    assert (SRC / "app.py").read_text().count("@callback(") == 5
    assert set(_callback_functions()) == CALLBACKS


def test_no_allow_duplicate_or_match():
    for path in SRC.glob("*.py"):
        text = path.read_text()
        assert "allow_duplicate" not in text, path.name
        assert "MATCH" not in text, path.name


def test_src_under_800_lines():
    total = sum(len(p.read_text().splitlines()) for p in SRC.rglob("*.py"))
    assert total < 800, f"src/ has {total} lines"

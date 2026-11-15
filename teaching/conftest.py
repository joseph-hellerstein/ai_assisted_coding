"""Shared test setup for the teaching edition.

Puts teaching/ on sys.path so tests import the app the same way the app
imports itself (`from src.storage import ...`), and provides `tmp_storage`,
which points storage at a temporary folder so every test starts empty.
"""
import sys
from pathlib import Path

import pytest

TEACHING_DIR = Path(__file__).parent
if str(TEACHING_DIR) not in sys.path:
    sys.path.insert(0, str(TEACHING_DIR))


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    import src.storage as storage

    monkeypatch.setattr(storage, "SURVEYS_DIR", tmp_path / "surveys")
    monkeypatch.setattr(storage, "RESPONSES_DIR", tmp_path / "responses")
    return tmp_path

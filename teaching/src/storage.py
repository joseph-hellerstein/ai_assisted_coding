"""Saving and loading surveys and responses as JSON files.

    surveys/<survey_id>.json
    data/responses/<survey_id>/<response_id>.json

Paths are relative to the teaching/ folder.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.models import Response, Survey

BASE_DIR = Path(__file__).parent.parent
SURVEYS_DIR = BASE_DIR / "surveys"
RESPONSES_DIR = BASE_DIR / "data" / "responses"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def save_survey(survey: Survey) -> None:
    _write_json(SURVEYS_DIR / f"{survey.id}.json", survey.to_dict())


def load_survey(survey_id: str) -> Survey | None:
    path = SURVEYS_DIR / f"{survey_id}.json"
    if not path.exists():
        return None
    return Survey.from_dict(json.loads(path.read_text()))


def list_surveys() -> list[dict]:
    """Every saved survey's id and title, sorted by title."""
    surveys = []
    for path in SURVEYS_DIR.glob("*.json"):
        data = json.loads(path.read_text())
        surveys.append({"id": data["id"], "title": data["title"]})
    return sorted(surveys, key=lambda s: (s["title"].lower(), s["id"]))


def save_response(response: Response) -> None:
    _write_json(RESPONSES_DIR / response.survey_id / f"{response.id}.json", response.to_dict())


def load_responses(survey_id: str) -> list[Response]:
    """Every response to a survey, oldest first."""
    folder = RESPONSES_DIR / survey_id
    responses = [Response.from_dict(json.loads(p.read_text())) for p in folder.glob("*.json")]
    return sorted(responses, key=lambda r: r.submitted_at)

"""Storage utilities for loading and saving surveys and responses."""

import json
import os
from pathlib import Path
from typing import Optional

from models import Survey, Response


# Base directory relative to this file
BASE_DIR = Path(__file__).parent.parent
SURVEYS_DIR = BASE_DIR / "surveys"
RESPONSES_DIR = BASE_DIR / "data" / "responses"


def ensure_dirs():
    """Ensure required directories exist."""
    SURVEYS_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)


def _survey_path(survey_id: str) -> Path:
    return SURVEYS_DIR / f"{survey_id}.json"


def _response_dir(survey_id: str) -> Path:
    d = RESPONSES_DIR / survey_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_survey(survey: Survey):
    """Save a survey to disk."""
    ensure_dirs()
    path = _survey_path(survey.id)
    with open(path, "w") as f:
        json.dump(survey.to_dict(), f, indent=2)


def load_survey(survey_id: str) -> Optional[Survey]:
    """Load a survey from disk. Returns None if not found."""
    path = _survey_path(survey_id)
    if not path.exists():
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return Survey.from_dict(data)


def list_surveys() -> list[dict]:
    """List all saved surveys (id and title only)."""
    ensure_dirs()
    surveys = []
    for path in SURVEYS_DIR.glob("*.json"):
        with open(path, "r") as f:
            data = json.load(f)
        surveys.append({
            "id": data["id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "question_count": len(data.get("questions", [])),
        })
    return sorted(surveys, key=lambda s: s["title"])


def save_response(response: Response):
    """Save a survey response to disk."""
    ensure_dirs()
    resp_dir = _response_dir(response.survey_id)
    path = resp_dir / f"{response.id}.json"
    with open(path, "w") as f:
        json.dump(response.to_dict(), f, indent=2)


def load_responses(survey_id: str) -> list[Response]:
    """Load all responses for a given survey."""
    resp_dir = RESPONSES_DIR / survey_id
    if not resp_dir.exists():
        return []
    responses = []
    for path in sorted(resp_dir.glob("*.json")):
        with open(path, "r") as f:
            data = json.load(f)
        responses.append(Response.from_dict(data))
    return responses


def delete_survey(survey_id: str):
    """Delete a survey and all its responses."""
    path = _survey_path(survey_id)
    if path.exists():
        os.remove(path)

    resp_dir = RESPONSES_DIR / survey_id
    if resp_dir.exists():
        import shutil
        shutil.rmtree(resp_dir)


def delete_response(response_id: str, survey_id: str):
    """Delete a specific response."""
    path = RESPONSES_DIR / survey_id / f"{response_id}.json"
    if path.exists():
        os.remove(path)
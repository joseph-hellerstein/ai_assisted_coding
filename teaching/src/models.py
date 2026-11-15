"""The data the app stores: surveys, their questions, and responses."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field, fields
from typing import Any


def _known_fields(cls, d: dict) -> dict:
    """Drop keys the class doesn't define, e.g. ones added by hand to a JSON file."""
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in names}


@dataclass
class Question:
    id: str
    type: str  # "text", "yesno" or "checkbox"
    text: str
    options: list[str] = field(default_factory=list)  # checkbox only

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Question:
        return cls(**_known_fields(cls, d))


@dataclass
class Survey:
    id: str
    title: str
    description: str = ""
    questions: list[Question] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Survey:
        questions = [Question.from_dict(q) for q in d.get("questions", [])]
        return cls(id=d["id"], title=d["title"], description=d.get("description", ""), questions=questions)


@dataclass
class Response:
    id: str  # internal id, e.g. "resp_1a2b3c4d"
    survey_id: str
    submitted_at: str
    respondent_id: str  # the 5 digits the respondent typed
    answers: dict[str, Any] = field(default_factory=dict)  # question id -> answer

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Response:
        return cls(**_known_fields(cls, d))


def generate_id(prefix: str) -> str:
    """A short random id, e.g. generate_id("srv_") -> "srv_1a2b3c4d"."""
    return prefix + uuid.uuid4().hex[:8]

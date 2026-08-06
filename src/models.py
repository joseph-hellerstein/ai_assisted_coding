"""Data models for the Survey Manager application."""
from __future__ import annotations


from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import json
from datetime import datetime


@dataclass
class Question:
    """Represents a single survey question."""
    id: str
    type: str  # "checkbox", "likert", "yesno", "numeric_scale", "text", "ranking", "multiselect", "matrix"
    text: str
    required: bool = True
    options: list[str] = field(default_factory=list)  # For checkbox, multiselect, ranking
    scale_min: int = 1       # For likert and numeric_scale
    scale_max: int = 5       # For likert and numeric_scale
    scale_label_min: str = ""  # Label for minimum scale value
    scale_label_max: str = ""  # Label for maximum scale value
    matrix_rows: list[str] = field(default_factory=list)  # For matrix questions
    matrix_cols: list[str] = field(default_factory=list)  # For matrix questions

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Survey:
    """Represents a complete survey."""
    id: str
    title: str
    description: str = ""
    questions: list[Question] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Survey":
        questions = [Question.from_dict(q) for q in data.get("questions", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            questions=questions,
        )


@dataclass
class Response:
    """Represents a single survey response."""
    id: str
    survey_id: str
    submitted_at: str
    answers: dict[str, Any] = field(default_factory=dict)  # question_id -> answer

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Response":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    suffix = timestamp[-6:]  # Use last 6 chars of microsecond for brevity
    return f"{prefix}{suffix}" if prefix else suffix
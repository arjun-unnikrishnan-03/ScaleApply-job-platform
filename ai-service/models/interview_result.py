"""
InterviewResult — the domain model for interview preparation.

This model is the OUTPUT contract of the Interview Agent.
It consumes CandidateProfile, JobDescription, ATSResult, and SkillGapResult
to provide a structured, tailored set of interview questions and evaluation criteria.

Design notes:
- Uses strict Pydantic validation (frozen, no extra fields).
- Enforces uniqueness of questions.
- Intentionally import-free of any LLM SDK.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=5000)]


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class QuestionDifficulty(str, Enum):
    """Normalized difficulty level for interview questions."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class QuestionCategory(str, Enum):
    """Normalized category for interview questions."""

    TECHNICAL = "Technical"
    PROJECT = "Project"
    BEHAVIORAL = "Behavioral"
    WEAK_AREA = "Weak Area"


# ──────────────────────────────────────────────
# Nested domain models
# ──────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    """
    A single interview question tailored to the candidate.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=True)

    question: NonEmptyStr
    category: QuestionCategory
    difficulty: QuestionDifficulty
    reason: NonEmptyStr


class EvaluationRubric(BaseModel):
    """
    Scoring criteria for the overall interview.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    criteria: NonEmptyStr
    passing_score_description: NonEmptyStr


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class InterviewResult(BaseModel):
    """
    The universal domain object representing tailored interview preparation.

    Immutability (frozen=True) guarantees that agents downstream cannot
    accidentally mutate shared state in concurrent pipelines.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # ── Questions ──────────────────────────────────────────────────────────
    technical_questions: list[InterviewQuestion] = Field(default_factory=list, max_length=20)
    project_questions: list[InterviewQuestion] = Field(default_factory=list, max_length=20)
    behavioral_questions: list[InterviewQuestion] = Field(default_factory=list, max_length=20)
    weak_area_questions: list[InterviewQuestion] = Field(default_factory=list, max_length=20)

    # ── Evaluation ─────────────────────────────────────────────────────────
    evaluation_rubric: list[EvaluationRubric] = Field(default_factory=list, max_length=10)
    explanation: NonEmptyStr

    # ── Metadata ───────────────────────────────────────────────────────────
    generated_at: str | None = None  # ISO8601 timestamp injected by agent
    candidate_name: str | None = None
    job_title: str | None = None

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator(
        "technical_questions",
        "project_questions",
        "behavioral_questions",
        "weak_area_questions",
        mode="before"
    )
    @classmethod
    def deduplicate_questions(cls, items: object) -> list[dict]:
        """Ensure questions are unique within a category based on the question text."""
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[dict] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            question_text = item.get("question", "")
            if not isinstance(question_text, str):
                continue
            lower = question_text.strip().lower()
            if lower and lower not in seen:
                seen.add(lower)
                result.append(item)
        return result

    @field_validator("evaluation_rubric", mode="before")
    @classmethod
    def require_rubric(cls, items: object) -> list[dict]:
        """Ensure evaluation rubric has at least one entry."""
        if not isinstance(items, list) or not items:
            raise ValueError("Evaluation rubric is required and cannot be empty.")
        return items

    # ── Computed helpers ───────────────────────────────────────────────────

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "technical_questions_count": len(self.technical_questions),
            "project_questions_count": len(self.project_questions),
            "behavioral_questions_count": len(self.behavioral_questions),
            "weak_area_questions_count": len(self.weak_area_questions),
            "evaluation_rubric_count": len(self.evaluation_rubric),
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
        }

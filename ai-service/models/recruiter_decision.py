"""
RecruiterDecision — the domain model for the final hiring recommendation.

This model is the OUTPUT contract of the Recruiter Agent.
It consumes all previous agent outputs (CandidateProfile, JobDescription,
ATSResult, SkillGapResult, InterviewResult) to provide a holistic hiring recommendation.

Design notes:
- Uses strict Pydantic validation (frozen, no extra fields).
- Enforces uniqueness of strengths/risks.
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
ConfidenceFloat = Annotated[float, Field(ge=0.0, le=1.0)]


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class Recommendation(str, Enum):
    """Normalized hiring recommendation levels."""

    STRONG_HIRE = "StrongHire"
    HIRE = "Hire"
    CONSIDER = "Consider"
    REJECT = "Reject"


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class RecruiterDecision(BaseModel):
    """
    The universal domain object representing the final recruiter decision.

    Immutability (frozen=True) guarantees that downstream systems cannot
    accidentally mutate shared state.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    # ── Core Decision ──────────────────────────────────────────────────────
    recommendation: Recommendation
    confidence: ConfidenceFloat

    # ── Qualitative Analysis ───────────────────────────────────────────────
    strengths: list[str] = Field(default_factory=list, max_length=20)
    risks: list[str] = Field(default_factory=list, max_length=20)
    interview_focus_areas: list[str] = Field(default_factory=list, max_length=20)

    # ── Summary / Justification ────────────────────────────────────────────
    summary: NonEmptyStr
    reasoning: NonEmptyStr

    # ── Metadata ───────────────────────────────────────────────────────────
    decided_at: str | None = None  # ISO8601 timestamp injected by agent
    candidate_name: str | None = None
    job_title: str | None = None

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator(
        "strengths",
        "risks",
        "interview_focus_areas",
        mode="before"
    )
    @classmethod
    def deduplicate_lists(cls, items: object) -> list[str]:
        """Strip, deduplicate, and discard blank entries while preserving original casing."""
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            clean = item.strip()
            lower = clean.lower()
            if clean and lower not in seen:
                seen.add(lower)
                result.append(clean)
        return result

    # ── Computed helpers ───────────────────────────────────────────────────

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "strengths_count": len(self.strengths),
            "risks_count": len(self.risks),
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
        }

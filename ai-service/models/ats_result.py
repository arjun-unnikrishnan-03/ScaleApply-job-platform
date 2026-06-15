"""
ATSResult — the core domain model for the ATS evaluation.

This model is the OUTPUT contract of the ATS Agent and the INPUT
for future services like Skill Gap Agent, Interview Agent, and Recruiter Agent.

Design notes:
- Uses strict Pydantic validation (frozen, no extra fields).
- Enforces list deduplication and score boundaries.
- Intentionally import-free of any LLM SDK.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=5000)]
ScoreFloat = Annotated[float, Field(ge=0.0, le=100.0)]


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class ATSResult(BaseModel):
    """
    The universal domain object representing an ATS evaluation.

    This compares a CandidateProfile against a JobDescription.

    Immutability (frozen=True) guarantees that agents downstream cannot
    accidentally mutate shared state in concurrent pipelines.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # ── Scoring ────────────────────────────────────────────────────────────
    score: ScoreFloat

    # ── Skills Analysis ────────────────────────────────────────────────────
    matched_skills: list[str] = Field(default_factory=list, max_length=100)
    missing_skills: list[str] = Field(default_factory=list, max_length=100)

    # ── Qualitative Analysis ───────────────────────────────────────────────
    strengths: list[str] = Field(default_factory=list, max_length=20)
    weaknesses: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)

    # ── Summary / Justification ────────────────────────────────────────────
    explanation: NonEmptyStr

    # ── Metadata ───────────────────────────────────────────────────────────
    evaluated_at: str | None = None  # ISO8601 timestamp injected by agent
    candidate_name: str | None = None
    job_title: str | None = None

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator(
        "matched_skills",
        "missing_skills",
        "strengths",
        "weaknesses",
        "recommendations",
        mode="before",
    )
    @classmethod
    def normalize_list(cls, items: object) -> list[str]:
        """Strip, deduplicate, and discard blank entries."""
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
                # Preserve original case for output, but deduplicate case-insensitively
                result.append(clean)
        return result

    # ── Computed helpers ───────────────────────────────────────────────────

    def is_strong_match(self, threshold: float = 75.0) -> bool:
        """Returns True if the score meets the strong match threshold."""
        return self.score >= threshold

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "score": self.score,
            "matched_skills_count": len(self.matched_skills),
            "missing_skills_count": len(self.missing_skills),
            "strengths_count": len(self.strengths),
            "weaknesses_count": len(self.weaknesses),
            "recommendations_count": len(self.recommendations),
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
        }

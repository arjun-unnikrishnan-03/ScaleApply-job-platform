"""
SkillGapResult — the domain model for skill gap analysis.

This model is the OUTPUT contract of the Skill Gap Agent.
It consumes ATSResult, CandidateProfile, and JobDescription to
provide a targeted learning path and priority order for missing skills.

Design notes:
- Uses strict Pydantic validation (frozen, no extra fields).
- Strongly typed roadmap rather than generic lists.
- Intentionally import-free of any LLM SDK.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=5000)]
PercentageFloat = Annotated[float, Field(ge=0.0, le=100.0)]
PositiveFloat = Annotated[float, Field(ge=0.0)]


# ──────────────────────────────────────────────
# Nested domain models
# ──────────────────────────────────────────────

class RoadmapStep(BaseModel):
    """
    A specific learning milestone or step in the roadmap.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_name: NonEmptyStr
    actionable_advice: NonEmptyStr
    estimated_weeks: PositiveFloat


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class SkillGapResult(BaseModel):
    """
    The universal domain object representing a skill gap analysis.

    Immutability (frozen=True) guarantees that agents downstream cannot
    accidentally mutate shared state in concurrent pipelines.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # ── High Level Metrics ─────────────────────────────────────────────────
    match_percentage: PercentageFloat
    estimated_learning_weeks: PositiveFloat

    # ── Skills Analysis ────────────────────────────────────────────────────
    missing_skills: list[str] = Field(default_factory=list, max_length=100)
    priority_order: list[str] = Field(default_factory=list, max_length=100)
    strengths: list[str] = Field(default_factory=list, max_length=50)

    # ── Actionable Path ────────────────────────────────────────────────────
    roadmap: list[RoadmapStep] = Field(default_factory=list, max_length=20)
    explanation: NonEmptyStr

    # ── Metadata ───────────────────────────────────────────────────────────
    analyzed_at: str | None = None  # ISO8601 timestamp injected by agent
    candidate_name: str | None = None
    job_title: str | None = None

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("missing_skills", "priority_order", "strengths", mode="before")
    @classmethod
    def normalize_list(cls, items: object) -> list[str]:
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

    @field_validator("roadmap", mode="before")
    @classmethod
    def deduplicate_roadmap(cls, items: object) -> list[dict]:
        """Ensure roadmap steps don't have duplicate skill names."""
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[dict] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            skill_name = item.get("skill_name", "")
            if not isinstance(skill_name, str):
                continue
            lower = skill_name.strip().lower()
            if lower and lower not in seen:
                seen.add(lower)
                result.append(item)
        return result

    # ── Computed helpers ───────────────────────────────────────────────────

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "match_percentage": self.match_percentage,
            "estimated_learning_weeks": self.estimated_learning_weeks,
            "missing_skills_count": len(self.missing_skills),
            "roadmap_steps_count": len(self.roadmap),
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
        }

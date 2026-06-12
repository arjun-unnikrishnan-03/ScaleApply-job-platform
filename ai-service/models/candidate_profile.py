"""
CandidateProfile — the core domain model for the AI Recruitment Platform.

All agent outputs, ATS comparisons, skill gap analyses, and interview
preparations will consume this single, strongly-typed object. It acts
as the universal "lingua franca" between every future microservice.

Design notes:
- All fields use Optional where data may be absent in a resume.
- Field validators enforce semantic constraints beyond type-safety.
- model_config forbids extra fields, making it safe to log and store.
- The class is intentionally import-free of any LLM SDK.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=2000)]
YearInt = Annotated[int, Field(ge=1950, le=2100)]


# ──────────────────────────────────────────────
# Nested domain models
# ──────────────────────────────────────────────

class DateRange(BaseModel):
    """
    Represents a half-open time interval.
    `end_date` is None when the position is current.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def end_after_start(self) -> "DateRange":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must be >= start_date ({self.start_date})."
            )
        return self


class Experience(BaseModel):
    """
    A single work experience entry.

    Future ATS Agent will compare required_experience years against the
    total duration derived from all Experience objects.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    company: NonEmptyStr
    title: NonEmptyStr
    location: str | None = None
    duration: DateRange | None = None
    responsibilities: list[str] = Field(default_factory=list, max_length=20)
    technologies_used: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("responsibilities", "technologies_used", mode="before")
    @classmethod
    def strip_and_deduplicate(cls, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            clean = item.strip()
            lower = clean.lower()
            if clean and lower not in seen:
                seen.add(lower)
                result.append(clean)
        return result


class Education(BaseModel):
    """
    An academic credential.

    Future Skill Gap Agent will use `field_of_study` to assess domain
    alignment between candidates and job requirements.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    institution: NonEmptyStr
    degree: NonEmptyStr
    field_of_study: str | None = None
    graduation_year: YearInt | None = None
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)

    @field_validator("gpa", mode="before")
    @classmethod
    def coerce_gpa(cls, v: object) -> float | None:
        """Accept GPA as string '3.8/4.0' or float 3.8."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            match = re.search(r"(\d+\.?\d*)", v)
            if match:
                return float(match.group(1))
        return None


class Project(BaseModel):
    """
    A portfolio or side project.

    Future Interview Agent will generate targeted technical questions
    based on `technologies` and `description`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr
    description: str | None = None
    technologies: list[str] = Field(default_factory=list, max_length=30)
    url: str | None = None

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if v and not re.match(r"^https?://", v):
            # Accept bare GitHub paths by prepending https
            return f"https://{v}" if "." in v else None
        return v or None


class Certification(BaseModel):
    """
    A professional certification or license.

    Future ATS Agent will match against job posting required_certifications.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr
    issuing_organization: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class CandidateProfile(BaseModel):
    """
    The universal domain object representing an extracted resume.

    This is the OUTPUT contract of the Resume Intelligence Agent and the
    INPUT contract for every downstream agent:

    - ATS Agent: compares CandidateProfile against JobDescription.
    - Skill Gap Agent: identifies missing skills and recommends learning paths.
    - Interview Agent: generates tailored technical and behavioral questions.
    - Recruiter Agent: scores and ranks multiple CandidateProfiles against a role.

    Immutability (frozen=True) guarantees that agents downstream cannot
    accidentally mutate shared state in concurrent pipelines.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    # ── Identity ───────────────────────────────────────────────────────────
    full_name: NonEmptyStr
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    location: str | None = None
    portfolio_url: str | None = None

    # ── Summary ────────────────────────────────────────────────────────────
    professional_summary: str | None = None

    # ── Skills ─────────────────────────────────────────────────────────────
    technical_skills: list[str] = Field(default_factory=list, max_length=100)
    soft_skills: list[str] = Field(default_factory=list, max_length=50)
    languages: list[str] = Field(default_factory=list, max_length=20)

    # ── Structured sections ────────────────────────────────────────────────
    experience: list[Experience] = Field(default_factory=list, max_length=30)
    education: list[Education] = Field(default_factory=list, max_length=10)
    projects: list[Project] = Field(default_factory=list, max_length=30)
    certifications: list[Certification] = Field(default_factory=list, max_length=20)

    # ── Metadata ───────────────────────────────────────────────────────────
    years_of_experience: float | None = Field(default=None, ge=0, le=60)
    extracted_at: str | None = None  # ISO8601 timestamp injected by agent
    source_file: str | None = None   # Original filename for traceability

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            return None  # Return None rather than raise — LLMs often hallucinate emails
        return v

    @field_validator("technical_skills", "soft_skills", "languages", mode="before")
    @classmethod
    def normalize_skill_list(cls, items: list[str]) -> list[str]:
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if isinstance(item, str):
                clean = item.strip()
                lower = clean.lower()
                if clean and lower not in seen:
                    seen.add(lower)
                    result.append(clean)
        return result

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def coerce_years(cls, v: object) -> float | None:
        """Accept '5+', '5 years', 5, 5.5 as floats."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            match = re.search(r"(\d+\.?\d*)", v)
            if match:
                return float(match.group(1))
        return None

    # ── Computed helpers ───────────────────────────────────────────────────

    def total_technologies(self) -> set[str]:
        """Aggregate all technologies mentioned across projects and experience."""
        techs: set[str] = set(t.lower() for t in self.technical_skills)
        for exp in self.experience:
            techs.update(t.lower() for t in exp.technologies_used)
        for proj in self.projects:
            techs.update(t.lower() for t in proj.technologies)
        return techs

    def is_complete(self) -> bool:
        """Heuristic check: a usable profile has at minimum name + one section."""
        return bool(
            self.full_name
            and (self.experience or self.education or self.technical_skills)
        )

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "full_name": self.full_name,
            "email": self.email,
            "years_of_experience": self.years_of_experience,
            "technical_skills_count": len(self.technical_skills),
            "experience_count": len(self.experience),
            "education_count": len(self.education),
            "projects_count": len(self.projects),
            "certifications_count": len(self.certifications),
            "is_complete": self.is_complete(),
        }

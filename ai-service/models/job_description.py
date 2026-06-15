"""
JobDescription — the core domain model for job posting intelligence.

This is the OUTPUT contract of the Job Intelligence Agent and the
INPUT contract for every downstream agent:

- ATS Agent:       compares CandidateProfile against JobDescription.
- Skill Gap Agent: identifies missing skills between a candidate and a role.
- Interview Agent: generates tailored questions based on the role requirements.
- Recruiter Agent: scores and ranks multiple CandidateProfiles against this posting.

Design notes:
- All fields use Optional where data may be absent in a job description.
- Field validators enforce semantic constraints beyond type-safety.
- model_config forbids extra fields, making it safe to log and store.
- The class is intentionally import-free of any LLM SDK.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=2000)]
PositiveFloat = Annotated[float, Field(ge=0.0, le=60.0)]


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class EmploymentType(str, Enum):
    """
    Normalized employment type enumeration.

    The LLM may return many surface forms ("Full Time", "full-time", "FT").
    The validator normalizes all of these before Pydantic coerces to this enum.
    """

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    """
    Seniority level derived from job description language.

    Future ATS Agent will use this alongside `experience_required`
    to gate candidate eligibility without re-parsing the original text.
    """

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    DIRECTOR = "director"
    UNKNOWN = "unknown"


# ──────────────────────────────────────────────
# Nested domain models
# ──────────────────────────────────────────────

class ExperienceRequirement(BaseModel):
    """
    Structured representation of required work experience.

    Separates the minimum and maximum years so that the ATS Agent
    can perform range comparisons against CandidateProfile.years_of_experience
    without custom parsing logic.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_years: float = Field(ge=0.0, le=60.0)
    max_years: float | None = Field(default=None, ge=0.0, le=60.0)
    level: ExperienceLevel = ExperienceLevel.UNKNOWN
    raw_text: str | None = None  # Original text, e.g. "5+ years"

    @model_validator(mode="after")
    def max_gte_min(self) -> "ExperienceRequirement":
        if self.max_years is not None and self.max_years < self.min_years:
            raise ValueError(
                f"max_years ({self.max_years}) must be >= min_years ({self.min_years})."
            )
        return self


class SalaryRange(BaseModel):
    """
    Optional structured compensation information.

    Future Recruiter Agent will use this for candidate/role alignment scoring.
    Kept optional because most job postings omit salary data.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    currency: str = "USD"
    period: str = "annual"  # "annual", "monthly", "hourly"
    raw_text: str | None = None

    @model_validator(mode="after")
    def max_gte_min(self) -> "SalaryRange":
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.max_amount < self.min_amount
        ):
            raise ValueError(
                f"max_amount ({self.max_amount}) must be >= min_amount ({self.min_amount})."
            )
        return self


class Benefit(BaseModel):
    """
    A single employment benefit or perk.

    Future Recruiter Agent may use benefits to assess offer competitiveness.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr
    description: str | None = None


# ──────────────────────────────────────────────
# Root domain object
# ──────────────────────────────────────────────

class JobDescription(BaseModel):
    """
    The universal domain object representing an extracted job posting.

    This is the OUTPUT contract of the Job Intelligence Agent and the
    INPUT contract for every downstream agent:

    - ATS Agent:       zip(CandidateProfile, JobDescription) → ATSResult
    - Skill Gap Agent: zip(CandidateProfile, JobDescription) → SkillGapReport
    - Interview Agent: JobDescription → list[Question]
    - Recruiter Agent: list[CandidateProfile] + JobDescription → RankedCandidates

    Immutability (frozen=True) guarantees that agents downstream cannot
    accidentally mutate shared state in concurrent pipelines.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    # ── Core identity (REQUIRED) ───────────────────────────────────────────
    title: NonEmptyStr

    # ── Organizational context ─────────────────────────────────────────────
    department: str | None = None
    company_name: str | None = None
    location: str | None = None
    remote_policy: str | None = None  # "remote", "hybrid", "on-site"

    # ── Employment characteristics ─────────────────────────────────────────
    employment_type: EmploymentType = EmploymentType.UNKNOWN

    # ── Experience ─────────────────────────────────────────────────────────
    experience_required: ExperienceRequirement | None = None

    # ── Skills ─────────────────────────────────────────────────────────────
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    preferred_skills: list[str] = Field(default_factory=list, max_length=100)
    technologies: list[str] = Field(default_factory=list, max_length=100)

    # ── Structured sections ────────────────────────────────────────────────
    responsibilities: list[str] = Field(default_factory=list, max_length=50)
    qualifications: list[str] = Field(default_factory=list, max_length=50)
    benefits: list[Benefit] = Field(default_factory=list, max_length=30)

    # ── Compensation ───────────────────────────────────────────────────────
    salary_range: SalaryRange | None = None

    # ── Summary ────────────────────────────────────────────────────────────
    summary: str | None = None

    # ── Metadata ───────────────────────────────────────────────────────────
    extracted_at: str | None = None   # ISO8601 timestamp injected by agent
    source_name: str | None = None    # Logical name for traceability

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def normalize_skill_list(cls, items: object) -> list[str]:
        """
        Normalize skill lists: strip whitespace, deduplicate case-insensitively,
        split comma-separated strings that LLMs sometimes emit as a single item.
        """
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            # Split on commas — LLMs sometimes emit "React, Node.js" as one string
            parts = [p.strip() for p in item.split(",")]
            for part in parts:
                lower = part.lower()
                if part and lower not in seen:
                    seen.add(lower)
                    result.append(part)
        return result

    @field_validator("technologies", mode="before")
    @classmethod
    def normalize_technologies(cls, items: object) -> list[str]:
        """Deduplicate technologies, preserving original casing of first occurrence."""
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            parts = [p.strip() for p in item.split(",")]
            for part in parts:
                lower = part.lower()
                if part and lower not in seen:
                    seen.add(lower)
                    result.append(part)
        return result

    @field_validator("responsibilities", "qualifications", mode="before")
    @classmethod
    def normalize_text_list(cls, items: object) -> list[str]:
        """Strip, deduplicate, and discard blank entries from free-text lists."""
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

    @field_validator("employment_type", mode="before")
    @classmethod
    def normalize_employment_type(cls, v: object) -> str:
        """
        Normalize LLM employment type surface forms to enum values.

        The LLM may return: "Full Time", "full-time", "FT", "Permanent",
        "Contract/Temp", etc. We map to canonical enum strings.
        """
        if v is None:
            return EmploymentType.UNKNOWN.value
        raw = str(v).lower().strip().replace("-", "_").replace(" ", "_")
        _mapping = {
            "full_time": EmploymentType.FULL_TIME.value,
            "fulltime": EmploymentType.FULL_TIME.value,
            "ft": EmploymentType.FULL_TIME.value,
            "permanent": EmploymentType.FULL_TIME.value,
            "part_time": EmploymentType.PART_TIME.value,
            "parttime": EmploymentType.PART_TIME.value,
            "pt": EmploymentType.PART_TIME.value,
            "contract": EmploymentType.CONTRACT.value,
            "contractor": EmploymentType.CONTRACT.value,
            "c2c": EmploymentType.CONTRACT.value,
            "internship": EmploymentType.INTERNSHIP.value,
            "intern": EmploymentType.INTERNSHIP.value,
            "freelance": EmploymentType.FREELANCE.value,
            "freelancer": EmploymentType.FREELANCE.value,
            "temporary": EmploymentType.TEMPORARY.value,
            "temp": EmploymentType.TEMPORARY.value,
        }
        return _mapping.get(raw, EmploymentType.UNKNOWN.value)

    @model_validator(mode="after")
    def required_skills_not_empty(self) -> "JobDescription":
        """
        Business rule: a usable job description must have at least one required skill.

        This is a WARN-level guard, not a hard failure — some postings legitimately
        list skills only in the responsibilities section. The validator raises only
        when both required_skills AND technologies are empty.
        """
        if not self.required_skills and not self.technologies:
            raise ValueError(
                "A job description must have at least one required_skill or technology. "
                "Both lists are empty — the extraction may have failed."
            )
        return self

    # ── Computed helpers ───────────────────────────────────────────────────

    def all_required_technologies(self) -> set[str]:
        """
        Union of required_skills and technologies — lowercase normalized.

        The ATS Agent will use this to compute candidate technology coverage
        without distinguishing between skills and technology stacks.
        """
        techs: set[str] = set(t.lower() for t in self.technologies)
        techs.update(s.lower() for s in self.required_skills)
        return techs

    def seniority_level(self) -> ExperienceLevel:
        """Return the seniority level from experience_required, or UNKNOWN."""
        if self.experience_required:
            return ExperienceLevel(self.experience_required.level)
        return ExperienceLevel.UNKNOWN

    def is_remote(self) -> bool:
        """True if the posting explicitly indicates full remote work."""
        if not self.remote_policy:
            return False
        return "remote" in self.remote_policy.lower()

    def summary_dict(self) -> dict:
        """Lightweight dict for logging — excludes large text fields."""
        return {
            "title": self.title,
            "department": self.department,
            "employment_type": self.employment_type,
            "required_skills_count": len(self.required_skills),
            "preferred_skills_count": len(self.preferred_skills),
            "technologies_count": len(self.technologies),
            "responsibilities_count": len(self.responsibilities),
            "qualifications_count": len(self.qualifications),
            "experience_min_years": (
                self.experience_required.min_years if self.experience_required else None
            ),
            "seniority_level": self.seniority_level(),
            "is_remote": self.is_remote(),
        }

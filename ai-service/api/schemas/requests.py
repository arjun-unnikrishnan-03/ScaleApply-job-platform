"""
Request schemas (DTOs) for the API layer.
These decouple the external HTTP interface from internal domain models.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResumeAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(
        ...,
        min_length=50,
        description="The raw text extracted from a resume.",
        examples=["Jane Doe — Senior Software Engineer\n5+ years Python, FastAPI..."],
    )


class JobAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(
        ...,
        min_length=50,
        description="The raw text of the job description.",
        examples=["Senior Backend Engineer at TechCorp — must have 3+ years Python..."],
    )


class ATSAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_profile: dict = Field(
        ...,
        description="The parsed CandidateProfile as a JSON-serializable dict (from /resume/analyze).",
    )
    job_description: dict = Field(
        ...,
        description="The parsed JobDescription as a JSON-serializable dict (from /job/analyze).",
    )


class SkillGapAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_profile: dict = Field(..., description="CandidateProfile dict from /resume/analyze.")
    job_description: dict = Field(..., description="JobDescription dict from /job/analyze.")
    ats_result: dict = Field(..., description="ATSResult dict from /ats/analyze.")


class InterviewGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_profile: dict = Field(..., description="CandidateProfile dict.")
    job_description: dict = Field(..., description="JobDescription dict.")
    ats_result: dict = Field(..., description="ATSResult dict.")
    skill_gap_result: dict = Field(..., description="SkillGapResult dict from /skill-gap/analyze.")


class RecruiterEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_profile: dict = Field(..., description="CandidateProfile dict.")
    job_description: dict = Field(..., description="JobDescription dict.")
    ats_result: dict = Field(..., description="ATSResult dict.")
    skill_gap_result: dict = Field(..., description="SkillGapResult dict.")
    interview_result: dict = Field(..., description="InterviewResult dict from /interview/generate.")


class KnowledgeQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(
        ...,
        min_length=1,
        description="The natural language question to search the knowledge base for.",
        examples=["What skills are most important for a backend engineer?"],
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of knowledge documents to retrieve.",
    )

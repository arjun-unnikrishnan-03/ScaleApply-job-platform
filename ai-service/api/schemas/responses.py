"""
Response schemas (DTOs) for the API layer.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str


class ResumeAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: dict[str, Any] = Field(..., description="The extracted CandidateProfile.")


class JobAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_description: dict[str, Any] = Field(..., description="The extracted JobDescription.")


class ATSAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ats_result: dict[str, Any] = Field(..., description="The ATSResult evaluation.")


class SkillGapAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_gap_result: dict[str, Any] = Field(..., description="The SkillGapResult analysis.")


class InterviewGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interview_result: dict[str, Any] = Field(..., description="The generated InterviewResult.")


class RecruiterEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recruiter_decision: dict[str, Any] = Field(..., description="The RecruiterDecision.")


class KnowledgeQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., description="The original query string.")
    documents: list[dict[str, Any]] = Field(..., description="Retrieved knowledge documents.")
    scores: list[float] = Field(..., description="Relevance scores for each document.")

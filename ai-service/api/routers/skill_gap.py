"""
Skill Gap router — POST /skill-gap/analyze
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from agents.skill_gap_agent import SkillGapAgent
from api.dependencies.agents import get_skill_gap_agent
from api.schemas.requests import SkillGapAnalysisRequest
from api.schemas.responses import SkillGapAnalysisResponse
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap"])


@router.post(
    "/analyze",
    response_model=SkillGapAnalysisResponse,
    summary="Skill gap analysis",
    description=(
        "Identifies missing skills, learning priorities, and estimated effort "
        "required for a candidate to meet a job's requirements, based on the ATS result."
    ),
)
async def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
    agent: SkillGapAgent = Depends(get_skill_gap_agent),
) -> SkillGapAnalysisResponse:
    candidate = CandidateProfile.model_validate(request.candidate_profile)
    job = JobDescription.model_validate(request.job_description)
    ats_result = ATSResult.model_validate(request.ats_result)

    result = agent.analyze(candidate=candidate, job=job, ats_result=ats_result)

    if not result.is_success:
        raise result.error

    skill_gap_result = result.unwrap()
    return SkillGapAnalysisResponse(skill_gap_result=skill_gap_result.model_dump(mode="json"))

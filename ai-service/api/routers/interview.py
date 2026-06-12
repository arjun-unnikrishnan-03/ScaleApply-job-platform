"""
Interview router — POST /interview/generate
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from agents.interview_agent import InterviewAgent
from api.dependencies.agents import get_interview_agent
from api.schemas.requests import InterviewGenerationRequest
from api.schemas.responses import InterviewGenerationResponse
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post(
    "/generate",
    response_model=InterviewGenerationResponse,
    summary="Generate interview preparation content",
    description=(
        "Generates personalized interview questions and preparation guidance for a candidate, "
        "covering technical, behavioral, and gap-focused question sets."
    ),
)
async def generate_interview(
    request: InterviewGenerationRequest,
    agent: InterviewAgent = Depends(get_interview_agent),
) -> InterviewGenerationResponse:
    candidate = CandidateProfile.model_validate(request.candidate_profile)
    job = JobDescription.model_validate(request.job_description)
    ats_result = ATSResult.model_validate(request.ats_result)
    skill_gap_result = SkillGapResult.model_validate(request.skill_gap_result)

    result = agent.generate(
        candidate=candidate,
        job=job,
        ats_result=ats_result,
        skill_gap_result=skill_gap_result,
    )

    if not result.is_success:
        raise result.error

    interview_result = result.unwrap()
    return InterviewGenerationResponse(interview_result=interview_result.model_dump(mode="json"))

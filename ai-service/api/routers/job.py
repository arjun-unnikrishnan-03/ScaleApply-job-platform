"""
Job router — POST /job/analyze
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from agents.job_agent import JobAgent
from api.dependencies.agents import get_job_agent
from api.schemas.requests import JobAnalysisRequest
from api.schemas.responses import JobAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job", tags=["Job"])


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse,
    summary="Analyze a job description",
    description=(
        "Parses a raw job description text using the JobAgent and returns "
        "a structured JobDescription object with extracted requirements."
    ),
)
async def analyze_job(
    request: JobAnalysisRequest,
    agent: JobAgent = Depends(get_job_agent),
) -> JobAnalysisResponse:
    result = agent.process_text(request.text)

    if not result.is_success:
        raise result.error

    job_description = result.unwrap()
    return JobAnalysisResponse(job_description=job_description.model_dump(mode="json"))

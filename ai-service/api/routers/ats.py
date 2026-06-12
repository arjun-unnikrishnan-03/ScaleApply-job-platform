"""
ATS router — POST /ats/analyze
"""
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from agents.ats_agent import ATSAgent
from api.dependencies.agents import get_ats_agent
from api.dependencies.queue import get_event_publisher, get_queue_service
from api.schemas.requests import ATSAnalysisRequest
from api.schemas.responses import ATSAnalysisResponse
from events.publisher import EventPublisher
from events.schemas import Event
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from services.queue_service import QueueService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ats", tags=["ATS"])


@router.post(
    "/analyze",
    response_model=ATSAnalysisResponse,
    summary="ATS compatibility analysis",
    description=(
        "Evaluates a CandidateProfile against a JobDescription using the ATSAgent "
        "and returns an ATSResult with a match score, matched/missing skills, "
        "and actionable recommendations."
    ),
)
async def analyze_ats(
    request: ATSAnalysisRequest,
    agent: ATSAgent = Depends(get_ats_agent),
) -> ATSAnalysisResponse:
    candidate = CandidateProfile.model_validate(request.candidate_profile)
    job = JobDescription.model_validate(request.job_description)

    result = agent.evaluate(candidate=candidate, job=job)

    if not result.is_success:
        raise result.error

    ats_result = result.unwrap()
    return ATSAnalysisResponse(ats_result=ats_result.model_dump(mode="json"))


@router.post(
    "/analyze/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze ATS compatibility asynchronously",
    description="Publishes an ATS analysis event to the queue and returns immediately.",
)
async def analyze_ats_async(
    request: ATSAnalysisRequest,
    publisher: EventPublisher = Depends(get_event_publisher),
) -> dict[str, str]:
    correlation_id = str(uuid4())
    event = Event(
        event_type="ats.processing.requested",
        correlation_id=correlation_id,
        payload=request.model_dump(mode="json"),
    )
    publisher.publish_event("ats.processing", event)
    return {"correlation_id": correlation_id}


@router.get(
    "/result/{correlation_id}",
    summary="Get ATS analysis result",
    description="Retrieves the status and result of an asynchronous ATS analysis.",
)
async def get_ats_result(
    correlation_id: str,
    queue_service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    result = queue_service.get_result(correlation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return result

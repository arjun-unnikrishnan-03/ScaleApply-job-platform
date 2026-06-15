"""
Resume router — POST /resume/analyze
"""
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from agents.resume_agent import ResumeAgent
from api.dependencies.agents import get_resume_agent
from api.dependencies.queue import get_event_publisher, get_queue_service
from api.schemas.requests import ResumeAnalysisRequest
from api.schemas.responses import ResumeAnalysisResponse
from events.publisher import EventPublisher
from events.schemas import Event
from services.queue_service import QueueService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post(
    "/analyze",
    response_model=ResumeAnalysisResponse,
    summary="Analyze a resume",
    description=(
        "Parses raw resume text using the ResumeAgent and returns a structured "
        "CandidateProfile extracted by the underlying LLM."
    ),
)
async def analyze_resume(
    request: ResumeAnalysisRequest,
    agent: ResumeAgent = Depends(get_resume_agent),
) -> ResumeAnalysisResponse:
    result = agent.process_text(request.text)

    if not result.is_success:
        raise result.error  # Domain errors are caught by the global handler

    profile = result.unwrap()
    return ResumeAnalysisResponse(profile=profile.model_dump(mode="json"))


@router.post(
    "/analyze/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze a resume asynchronously",
    description="Publishes a resume analysis event to the queue and returns immediately.",
)
async def analyze_resume_async(
    request: ResumeAnalysisRequest,
    publisher: EventPublisher = Depends(get_event_publisher),
) -> dict[str, str]:
    correlation_id = str(uuid4())
    event = Event(
        event_type="resume.processing.requested",
        correlation_id=correlation_id,
        payload=request.model_dump(mode="json"),
    )
    publisher.publish_event("resume.processing", event)
    return {"correlation_id": correlation_id}


@router.get(
    "/result/{correlation_id}",
    summary="Get resume analysis result",
    description="Retrieves the status and result of an asynchronous resume analysis.",
)
async def get_resume_result(
    correlation_id: str,
    queue_service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    result = queue_service.get_result(correlation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return result

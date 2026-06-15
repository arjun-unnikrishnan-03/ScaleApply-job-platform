"""
Recruiter router — POST /recruiter/evaluate
"""
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from agents.recruiter_agent import RecruiterAgent
from api.dependencies.agents import get_recruiter_agent
from api.dependencies.queue import get_event_publisher, get_queue_service
from api.schemas.requests import RecruiterEvaluationRequest
from api.schemas.responses import RecruiterEvaluationResponse
from events.publisher import EventPublisher
from events.schemas import Event
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from models.interview_result import InterviewResult
from services.queue_service import QueueService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


@router.post(
    "/evaluate",
    response_model=RecruiterEvaluationResponse,
    summary="Final recruiter evaluation",
    description=(
        "Synthesizes all previously generated intelligence (ATS, skill gap, interview) "
        "to produce a holistic final hiring recommendation from the RecruiterAgent."
    ),
)
async def evaluate_candidate(
    request: RecruiterEvaluationRequest,
    agent: RecruiterAgent = Depends(get_recruiter_agent),
) -> RecruiterEvaluationResponse:
    candidate = CandidateProfile.model_validate(request.candidate_profile)
    job = JobDescription.model_validate(request.job_description)
    ats_result = ATSResult.model_validate(request.ats_result)
    skill_gap_result = SkillGapResult.model_validate(request.skill_gap_result)
    interview_result = InterviewResult.model_validate(request.interview_result)

    result = agent.evaluate(
        candidate=candidate,
        job=job,
        ats_result=ats_result,
        skill_gap_result=skill_gap_result,
        interview_result=interview_result,
    )

    if not result.is_success:
        raise result.error

    decision = result.unwrap()
    return RecruiterEvaluationResponse(recruiter_decision=decision.model_dump(mode="json"))


@router.post(
    "/evaluate/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Holistic recruiter evaluation asynchronously",
    description="Publishes a recruiter evaluation event to the queue and returns immediately.",
)
async def evaluate_candidate_async(
    request: RecruiterEvaluationRequest,
    publisher: EventPublisher = Depends(get_event_publisher),
) -> dict[str, str]:
    correlation_id = str(uuid4())
    event = Event(
        event_type="recruiter.processing.requested",
        correlation_id=correlation_id,
        payload=request.model_dump(mode="json"),
    )
    publisher.publish_event("recruiter.processing", event)
    return {"correlation_id": correlation_id}


@router.get(
    "/result/{correlation_id}",
    summary="Get recruiter evaluation result",
    description="Retrieves the status and result of an asynchronous recruiter evaluation.",
)
async def get_recruiter_result(
    correlation_id: str,
    queue_service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    result = queue_service.get_result(correlation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return result

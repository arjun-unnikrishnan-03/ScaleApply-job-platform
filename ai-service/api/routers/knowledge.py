"""
Knowledge router — POST /knowledge/query
"""
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from agents.knowledge_agent import KnowledgeAgent
from api.dependencies.agents import get_knowledge_agent
from api.dependencies.queue import get_event_publisher, get_queue_service
from api.schemas.requests import KnowledgeQueryRequest
from api.schemas.responses import KnowledgeQueryResponse
from events.publisher import EventPublisher
from events.schemas import Event
from services.queue_service import QueueService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
    summary="Query the knowledge base",
    description=(
        "Performs a RAG-based search against the internal knowledge base and "
        "synthesizes an answer using the KnowledgeAgent. Suitable for questions "
        "about ATS best practices, interview preparation, and career guidance."
    ),
)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    agent: KnowledgeAgent = Depends(get_knowledge_agent),
) -> KnowledgeQueryResponse:
    result = agent.ask(request.query)

    if not result.is_success:
        raise result.error

    knowledge_response = result.unwrap()
    return KnowledgeQueryResponse(
        query=request.query,
        documents=[{"content": knowledge_response.answer, "sources": knowledge_response.sources}],
        scores=[knowledge_response.confidence],
    )


@router.post(
    "/query/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Query the knowledge base asynchronously",
    description="Publishes a knowledge query event to the queue and returns immediately.",
)
async def query_knowledge_async(
    request: KnowledgeQueryRequest,
    publisher: EventPublisher = Depends(get_event_publisher),
) -> dict[str, str]:
    correlation_id = str(uuid4())
    event = Event(
        event_type="knowledge.processing.requested",
        correlation_id=correlation_id,
        payload=request.model_dump(mode="json"),
    )
    publisher.publish_event("knowledge.processing", event)
    return {"correlation_id": correlation_id}


@router.get(
    "/result/{correlation_id}",
    summary="Get knowledge query result",
    description="Retrieves the status and result of an asynchronous knowledge query.",
)
async def get_knowledge_result(
    correlation_id: str,
    queue_service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    result = queue_service.get_result(correlation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return result

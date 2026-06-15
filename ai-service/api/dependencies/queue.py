from __future__ import annotations

from functools import lru_cache

from events.publisher import EventPublisher
from services.queue_service import QueueService


@lru_cache(maxsize=1)
def _get_queue_service() -> QueueService:
    """Create and cache the QueueService singleton."""
    return QueueService()


@lru_cache(maxsize=1)
def _get_event_publisher() -> EventPublisher:
    """Create and cache the EventPublisher singleton."""
    qs = _get_queue_service()
    return EventPublisher(qs)


def get_queue_service() -> QueueService:
    """FastAPI dependency resolving the QueueService."""
    return _get_queue_service()


def get_event_publisher() -> EventPublisher:
    """FastAPI dependency resolving the EventPublisher."""
    return _get_event_publisher()

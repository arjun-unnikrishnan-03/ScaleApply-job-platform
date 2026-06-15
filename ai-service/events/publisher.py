from __future__ import annotations

import logging
from events.schemas import Event
from services.queue_service import QueueService

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Component for publishing structured events into the messaging backplane.
    """

    def __init__(self, queue_service: QueueService) -> None:
        self.queue_service = queue_service

    def publish_event(self, stream: str, event: Event) -> str:
        """
        Publishes a strongly typed event to the targeted stream.
        """
        logger.info("Publishing event %s (%s) to stream %s", event.event_id, event.event_type, stream)
        return self.queue_service.publish(stream, event)

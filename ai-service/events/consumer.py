from __future__ import annotations

import logging
from typing import List, Tuple

from events.schemas import Event
from services.queue_service import QueueService

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Component for reading events from Redis Streams via consumer groups.
    """

    def __init__(self, queue_service: QueueService) -> None:
        self.queue_service = queue_service

    def setup_group(self, stream: str, group: str) -> None:
        """
        Guarantees that a consumer group exists for the given stream.
        """
        self.queue_service.create_consumer_group(stream, group)

    def read_events(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 2000,
    ) -> List[Tuple[str, Event]]:
        """
        Polls the stream for new events using the consumer group.
        Returns a list of tuples: (message_id_str, Event).
        """
        client = self.queue_service.client
        results: List[Tuple[str, Event]] = []

        try:
            # We read from the stream using XREADGROUP.
            # Passing '>' reads messages that have never been delivered to any other consumer.
            streams_query = {stream: ">"}
            response = client.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams=streams_query,
                count=count,
                block=block_ms,
            )

            if not response:
                return results

            # Response structure: [[stream_name_bytes, [(message_id_bytes, fields_dict)]]]
            for stream_entry in response:
                stream_name = stream_entry[0].decode("utf-8") if isinstance(stream_entry[0], bytes) else str(stream_entry[0])
                messages = stream_entry[1]
                for msg_id, fields in messages:
                    msg_id_str = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
                    
                    # Deserialize fields into event object
                    event = Event.from_redis_dict(fields)
                    results.append((msg_id_str, event))

        except Exception as e:
            logger.error("Error reading events from stream %s (group: %s): %s", stream, group, e)

        return results

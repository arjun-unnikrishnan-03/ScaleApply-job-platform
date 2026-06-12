from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis
from config.settings import settings
from events.schemas import Event

logger = logging.getLogger(__name__)


class QueueService:
    """
    Service wrapping Redis Stream queueing operations and cache results.
    """

    def __init__(self, host: str | None = None, port: int | None = None, db: int | None = None) -> None:
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.db = db if db is not None else settings.redis_db
        # Lazy connection initialization
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            # We connect to Redis
            logger.info("Initializing Redis client")
            if settings.redis_url:
                self._client = redis.Redis.from_url(
                    settings.redis_url,
                    decode_responses=False,
                )
            else:
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=False,  # Keep as bytes for stream reads, we decode ourselves
                )
        return self._client

    def ping(self) -> bool:
        """Pings Redis to test connectivity."""
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.warning("Failed to ping Redis: %s", e)
            return False

    def publish(self, stream: str, event: Event) -> str:
        """
        Publishes an event to a Redis Stream.
        Returns the Redis auto-generated message ID.
        """
        try:
            fields = event.to_redis_dict()
            message_id = self.client.xadd(stream, fields)
            msg_id_str = message_id.decode("utf-8") if isinstance(message_id, bytes) else str(message_id)
            logger.info("Published event %s to stream %s with ID %s", event.event_id, stream, msg_id_str)
            return msg_id_str
        except Exception as e:
            logger.error("Error publishing event to stream %s: %s", stream, e)
            raise

    def get_queue_depth(self, stream: str) -> int:
        """
        Returns the number of elements in the stream.
        """
        try:
            return int(self.client.xlen(stream))
        except redis.exceptions.ResponseError as e:
            # If stream doesn't exist yet, return 0
            if "no such key" in str(e).lower():
                return 0
            raise
        except Exception as e:
            logger.warning("Error reading depth for stream %s: %s", stream, e)
            return 0

    def create_consumer_group(self, stream: str, group: str) -> bool:
        """
        Creates a consumer group. If the stream doesn't exist, it is created.
        Returns True if created or already exists.
        """
        try:
            self.client.xgroup_create(stream, group, id="0", mkstream=True)
            logger.info("Created consumer group %s for stream %s", group, stream)
            return True
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Consumer group already exists, this is fine
                return True
            logger.error("Error creating consumer group: %s", e)
            return False
        except Exception as e:
            logger.error("Failed to create consumer group: %s", e)
            return False

    def ack_message(self, stream: str, group: str, message_id: str) -> None:
        """
        Acknowledges a message in a consumer group.
        """
        try:
            self.client.xack(stream, group, message_id)
            # Optionally delete the acknowledged message to keep the stream size under control
            self.client.xdel(stream, message_id)
        except Exception as e:
            logger.warning("Failed to ACK message %s: %s", message_id, e)

    def set_result(self, correlation_id: str, status: str, result: Any = None, error: str | None = None, attempts: int = 1) -> None:
        """
        Persists task processing status and payload.
        """
        key = f"result:{correlation_id}"
        payload = {
            "correlation_id": correlation_id,
            "status": status,
            "result": result,
            "error": error,
            "attempts": attempts,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            # Store in Redis with a 24-hour expiration time (86400 seconds)
            self.client.setex(key, 86400, json.dumps(payload))
        except Exception as e:
            logger.error("Failed to save result for %s: %s", correlation_id, e)

    def get_result(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a task processing result from the cache.
        """
        key = f"result:{correlation_id}"
        try:
            data = self.client.get(key)
            if data is None:
                return None
            str_data = data.decode("utf-8") if isinstance(data, bytes) else str(data)
            return dict(json.loads(str_data))
        except Exception as e:
            logger.warning("Error fetching result for %s: %s", correlation_id, e)
            return None

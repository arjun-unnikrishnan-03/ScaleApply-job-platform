from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    Strongly typed event model for asynchronous processing.
    Ensures consistent metadata and serializability across services and workers.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_redis_dict(self) -> dict[str, str]:
        """
        Serializes the event into a flat string dictionary for Redis Streams.
        """
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": json.dumps(self.payload),
        }

    @classmethod
    def from_redis_dict(cls, data: dict[bytes | str, bytes | str]) -> Event:
        """
        Deserializes a Redis Stream message dictionary back into an Event.
        """
        # Convert all bytes/keys/values to string
        str_data: dict[str, str] = {}
        for k, v in data.items():
            key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
            val = v.decode("utf-8") if isinstance(v, bytes) else str(v)
            str_data[key] = val

        payload_str = str_data.get("payload", "{}")
        try:
            payload = json.loads(payload_str)
        except Exception:
            payload = {}

        return cls(
            event_id=str_data.get("event_id", str(uuid4())),
            correlation_id=str_data.get("correlation_id", str(uuid4())),
            timestamp=str_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type=str_data.get("event_type", "unknown"),
            payload=payload,
        )

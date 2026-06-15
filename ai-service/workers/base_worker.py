from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

from events.consumer import EventConsumer
from events.schemas import Event
from services.queue_service import QueueService

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Abstract base worker defining the asynchronous consumer loop,
    retry strategies, dead-lettering, and metrics monitoring.
    """

    def __init__(
        self,
        queue_service: QueueService,
        stream: str,
        group: str = "workers-group",
        consumer_name: str | None = None,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_multiplier: float = 2.0,
    ) -> None:
        self.queue_service = queue_service
        self.stream = stream
        self.group = group
        self.consumer_name = consumer_name or f"worker-{stream}-{int(time.time())}"
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier

        self.consumer = EventConsumer(queue_service)
        self.is_running = False

    @abstractmethod
    def process_payload(self, payload: Dict[str, Any]) -> Any:
        """
        Executes the business logic / agent pipeline for this event.
        Must return a JSON-serializable dictionary or raise an exception.
        """
        pass

    def setup(self) -> None:
        """Initializes the consumer group."""
        logger.info("Setting up consumer group %s for stream %s", self.group, self.stream)
        self.consumer.setup_group(self.stream, self.group)

    def start(self, once: bool = False) -> None:
        """
        Starts the worker consumption loop.
        once=True processes a single batch and returns (useful for testing).
        """
        self.setup()
        self.is_running = True
        logger.info("Worker %s started listening on %s", self.consumer_name, self.stream)

        try:
            while self.is_running:
                events = self.consumer.read_events(
                    stream=self.stream,
                    group=self.group,
                    consumer_name=self.consumer_name,
                    count=1,
                    block_ms=1000,
                )

                for msg_id, event in events:
                    self._handle_event_with_retries(msg_id, event)

                if once:
                    break
        except KeyboardInterrupt:
            logger.info("Shutdown requested.")
        finally:
            self.is_running = False
            logger.info("Worker %s stopped.", self.consumer_name)

    def stop(self) -> None:
        self.is_running = False

    def _handle_event_with_retries(self, msg_id: str, event: Event) -> None:
        correlation_id = event.correlation_id
        logger.info("Worker started processing event %s (correlation_id: %s)", event.event_id, correlation_id)
        
        start_time = time.time()
        self.queue_service.set_result(correlation_id, "processing", attempts=1)

        attempts = 0
        success = False
        result = None
        error_msg = ""

        while attempts < self.max_retries:
            attempts += 1
            try:
                # Update status with current attempt count
                self.queue_service.set_result(correlation_id, "processing", attempts=attempts)
                
                # Execute the actual worker workload
                result = self.process_payload(event.payload)
                success = True
                break
            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    "Attempt %s/%s failed for event %s. Error: %s",
                    attempts,
                    self.max_retries,
                    event.event_id,
                    error_msg,
                )
                self._record_metric("retries_total")
                
                # Apply exponential backoff if not the final attempt
                if attempts < self.max_retries:
                    sleep_duration = self.backoff_base * (self.backoff_multiplier ** (attempts - 1))
                    logger.info("Sleeping for %s seconds before retry...", sleep_duration)
                    time.sleep(sleep_duration)

        latency_ms = int((time.time() - start_time) * 1000)

        if success:
            logger.info("Event %s processed successfully in %sms", event.event_id, latency_ms)
            self.queue_service.set_result(correlation_id, "completed", result=result, attempts=attempts)
            self.queue_service.ack_message(self.stream, self.group, msg_id)
            self._record_metric("successes_total")
            self._record_latency(latency_ms)
        else:
            logger.error("Event %s failed permanently after %s attempts", event.event_id, attempts)
            self.queue_service.set_result(correlation_id, "failed", error=error_msg, attempts=attempts)
            
            # Route to dead-letter queue (DLQ)
            self._route_to_dlq(event, error_msg, attempts)
            
            # Acknowledge to clear it from the stream PEL so workers can move on
            self.queue_service.ack_message(self.stream, self.group, msg_id)
            self._record_metric("failures_total")

    def _route_to_dlq(self, event: Event, error_msg: str, attempts: int) -> None:
        """
        Publishes the poisoned event into the dead_letter_queue stream.
        """
        dlq_event = Event(
            event_type=f"dlq.{event.event_type}",
            correlation_id=event.correlation_id,
            payload={
                "original_event": event.model_dump(),
                "error": error_msg,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "attempts": attempts,
                "source_stream": self.stream,
            }
        )
        try:
            self.queue_service.publish("dead_letter_queue", dlq_event)
            logger.info("Event %s dead-lettered to dead_letter_queue", event.event_id)
        except Exception as e:
            logger.error("Critical: Failed to route event %s to dead-letter queue: %s", event.event_id, e)

    def _record_metric(self, metric_name: str) -> None:
        """Records metric counts in Redis hash."""
        try:
            key = f"metrics:worker:{self.stream}"
            self.queue_service.client.hincrby(key, metric_name, 1)
        except Exception as e:
            logger.debug("Failed to record metric %s: %s", metric_name, e)

    def _record_latency(self, latency_ms: int) -> None:
        """Saves latency metric in Redis."""
        try:
            key = f"metrics:worker:{self.stream}"
            # Keep latest processing latency
            self.queue_service.client.hset(key, "last_processing_latency_ms", latency_ms)
        except Exception as e:
            logger.debug("Failed to record latency: %s", e)

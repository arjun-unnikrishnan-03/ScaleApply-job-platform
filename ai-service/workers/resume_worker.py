from __future__ import annotations

import logging
from typing import Any, Dict

from api.dependencies.providers import get_llm_provider
from agents.resume_agent import ResumeAgent
from services.queue_service import QueueService
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class ResumeWorker(BaseWorker):
    """
    Worker for parsing and analyzing resumes asynchronously.
    Consumes from the 'resume.processing' stream.
    """

    def __init__(
        self,
        queue_service: QueueService,
        group: str = "workers-group",
        consumer_name: str | None = None,
    ) -> None:
        super().__init__(
            queue_service=queue_service,
            stream="resume.processing",
            group=group,
            consumer_name=consumer_name,
        )
        # Initialize agent with globally configured LLM provider
        provider = get_llm_provider()
        self.agent = ResumeAgent(provider=provider)

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        """
        Executes ResumeAgent on the payload.
        """
        text = payload.get("text")
        if not text:
            raise ValueError("Payload missing required 'text' field.")

        logger.info("Executing ResumeAgent process_text...")
        result = self.agent.process_text(text)

        if not result.is_success:
            logger.error("ResumeAgent processing failed: %s", result.error)
            raise result.error

        profile = result.unwrap()
        return profile.model_dump(mode="json")


if __name__ == "__main__":
    # Standard entry point to run the worker stand-alone
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    qs = QueueService()
    worker = ResumeWorker(qs)
    worker.start()

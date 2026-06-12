from __future__ import annotations

import logging
from typing import Any, Dict

from api.dependencies.providers import get_llm_provider
from agents.ats_agent import ATSAgent
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from services.queue_service import QueueService
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class ATSWorker(BaseWorker):
    """
    Worker for executing ATS compatibility analysis asynchronously.
    Consumes from the 'ats.processing' stream.
    """

    def __init__(
        self,
        queue_service: QueueService,
        group: str = "workers-group",
        consumer_name: str | None = None,
    ) -> None:
        super().__init__(
            queue_service=queue_service,
            stream="ats.processing",
            group=group,
            consumer_name=consumer_name,
        )
        provider = get_llm_provider()
        self.agent = ATSAgent(provider=provider)

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        """
        Executes ATSAgent on the payload.
        """
        candidate_data = payload.get("candidate_profile")
        job_data = payload.get("job_description")

        if not candidate_data or not job_data:
            raise ValueError("Payload missing required 'candidate_profile' or 'job_description' fields.")

        # Validate inputs into domain models
        candidate = CandidateProfile.model_validate(candidate_data)
        job = JobDescription.model_validate(job_data)

        logger.info("Executing ATSAgent evaluate...")
        result = self.agent.evaluate(candidate=candidate, job=job)

        if not result.is_success:
            logger.error("ATSAgent evaluation failed: %s", result.error)
            raise result.error

        ats_result = result.unwrap()
        return ats_result.model_dump(mode="json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    qs = QueueService()
    worker = ATSWorker(qs)
    worker.start()

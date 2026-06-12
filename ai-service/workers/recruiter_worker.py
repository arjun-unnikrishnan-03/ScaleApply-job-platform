from __future__ import annotations

import logging
from typing import Any, Dict

from api.dependencies.providers import get_llm_provider
from agents.recruiter_agent import RecruiterAgent
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from models.interview_result import InterviewResult
from services.queue_service import QueueService
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class RecruiterWorker(BaseWorker):
    """
    Worker for performing holistic recruiter evaluations asynchronously.
    Consumes from the 'recruiter.processing' stream.
    """

    def __init__(
        self,
        queue_service: QueueService,
        group: str = "workers-group",
        consumer_name: str | None = None,
    ) -> None:
        super().__init__(
            queue_service=queue_service,
            stream="recruiter.processing",
            group=group,
            consumer_name=consumer_name,
        )
        provider = get_llm_provider()
        self.agent = RecruiterAgent(provider=provider)

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        """
        Executes RecruiterAgent on the payload.
        """
        required_keys = [
            "candidate_profile",
            "job_description",
            "ats_result",
            "skill_gap_result",
            "interview_result",
        ]
        for key in required_keys:
            if key not in payload:
                raise ValueError(f"Payload missing required '{key}' field.")

        # Validate inputs into domain models
        candidate = CandidateProfile.model_validate(payload["candidate_profile"])
        job = JobDescription.model_validate(payload["job_description"])
        ats_result = ATSResult.model_validate(payload["ats_result"])
        skill_gap_result = SkillGapResult.model_validate(payload["skill_gap_result"])
        interview_result = InterviewResult.model_validate(payload["interview_result"])

        logger.info("Executing RecruiterAgent evaluate...")
        result = self.agent.evaluate(
            candidate=candidate,
            job=job,
            ats_result=ats_result,
            skill_gap_result=skill_gap_result,
            interview_result=interview_result,
        )

        if not result.is_success:
            logger.error("RecruiterAgent evaluation failed: %s", result.error)
            raise result.error

        decision = result.unwrap()
        return decision.model_dump(mode="json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    qs = QueueService()
    worker = RecruiterWorker(qs)
    worker.start()

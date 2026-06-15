"""
SkillGapAgent — the Skill Gap Intelligence Agent.

This is the APPLICATION LAYER orchestrator for skill gap analysis. It coordinates:
  1. Prompt building (via SkillGapPrompt)
  2. LLM invocation (via LLMProvider interface)
  3. JSON extraction + Pydantic validation
  4. Result wrapping (via AgentResult monad)

DESIGN INVARIANTS:
- The agent depends ONLY on abstractions (LLMProvider).
- The agent NEVER raises exceptions to the caller — it returns AgentResult.
- Consumes CandidateProfile, JobDescription, and ATSResult strictly.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from core.exceptions import (
    ExtractionError,
    ProviderError,
    RecruitmentError,
    ValidationError,
)
from core.result import AgentResult
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from prompts.skill_gap_prompt import SkillGapPrompt
from providers.base import GenerationConfig, LLMProvider

logger = logging.getLogger(__name__)


class SkillGapAgent:
    """
    Skill Gap Intelligence Agent.

    Evaluates a CandidateProfile, JobDescription, and ATSResult to produce
    a strictly validated SkillGapResult.
    """

    def __init__(
        self,
        provider: LLMProvider,
        prompt: SkillGapPrompt | None = None,
        generation_config: GenerationConfig | None = None,
    ) -> None:
        """
        Dependency-injected constructor.

        Args:
            provider: Any LLMProvider implementation.
            prompt: Override for custom/experimental prompts.
            generation_config: Override LLM generation parameters.
        """
        self._provider = provider
        self._prompt = prompt or SkillGapPrompt()
        self._generation_config = generation_config or GenerationConfig(
            temperature=0.2,  # Slight creativity allowed for actionable advice
            max_output_tokens=4096,
            response_format="json",
        )

        logger.info(
            "SkillGapAgent initialized | provider=%s | prompt_version=%s",
            provider.get_model_name(),
            self._prompt.version,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, candidate: CandidateProfile, job: JobDescription, ats_result: ATSResult) -> AgentResult[SkillGapResult]:
        """
        Analyze skill gaps for a candidate.

        The pipeline is:
            Build prompt → Call LLM → Extract JSON → Validate

        Args:
            candidate: A validated CandidateProfile domain object.
            job: A validated JobDescription domain object.
            ats_result: A validated ATSResult domain object.

        Returns:
            AgentResult.success(SkillGapResult) on success.
            AgentResult.failure(RecruitmentError) on any failure.
        """
        c_name = candidate.full_name
        j_title = job.title
        logger.info("Analyzing skill gaps for candidate '%s' against job '%s'", c_name, j_title)

        try:
            # ── Stage 1: Build prompt ─────────────────────────────────────
            prompt_str = self._build_prompt(candidate, job, ats_result)

            # ── Stage 2: Call LLM ─────────────────────────────────────────
            response = self._call_provider(prompt_str)

            # ── Stage 3: Extract JSON ──────────────────────────────────────
            data = self._extract_json(response.content)

            # ── Stage 4: Validate with Pydantic ──────────────────────────
            gap_result = self._validate(data=data, candidate_name=c_name, job_title=j_title)

            logger.info(
                "Analysis complete: missing_skills=%d | candidate='%s' | job='%s'",
                len(gap_result.missing_skills),
                c_name,
                j_title,
            )
            return AgentResult.success(
                value=gap_result,
                metadata={
                    "candidate_name": c_name,
                    "job_title": j_title,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "prompt_version": self._prompt.version,
                },
            )

        except RecruitmentError as exc:
            logger.warning("SkillGapAgent pipeline error: %s", exc)
            return AgentResult.failure(
                error=exc,
                metadata={"candidate_name": c_name, "job_title": j_title}
            )

        except Exception as exc:
            logger.exception("Unexpected error in SkillGapAgent: %s", exc)
            wrapped = RecruitmentError(
                message=f"Unexpected agent error: {exc}",
                details={"exception_type": type(exc).__name__},
            )
            return AgentResult.failure(
                error=wrapped,
                metadata={"candidate_name": c_name, "job_title": j_title}
            )

    # ── Private pipeline stages ───────────────────────────────────────────────

    def _build_prompt(self, candidate: CandidateProfile, job: JobDescription, ats_result: ATSResult) -> str:
        """Stage 1: Render the evaluation prompt."""
        return self._prompt.build(candidate=candidate, job=job, ats_result=ats_result)

    def _call_provider(self, prompt: str):
        """Stage 2: Invoke the LLM via the provider interface."""
        try:
            response = self._provider.generate(prompt, config=self._generation_config)
            logger.debug(
                "Provider response: model=%s | tokens_in=%d | tokens_out=%d",
                response.model,
                response.input_tokens,
                response.output_tokens,
            )
            return response
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Provider call failed: {exc}") from exc

    def _extract_json(self, raw_content: str) -> dict[str, Any]:
        """
        Stage 3: Extract a JSON dict from the LLM response.
        """
        if not raw_content:
            raise ExtractionError(raw_content or "")

        content = raw_content.strip()

        # Strip markdown code fences if present
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
        content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
        content = content.strip()

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            raise ExtractionError(raw_content)

        json_str = content[start : end + 1]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse failed: %s | raw=%s...", exc, raw_content[:200])
            raise ExtractionError(raw_content) from exc

        if not isinstance(data, dict):
            raise ExtractionError(raw_content)

        return data

    def _validate(self, data: dict[str, Any], candidate_name: str, job_title: str) -> SkillGapResult:
        """
        Stage 4: Validate extracted dict against the SkillGapResult schema.
        """
        data["candidate_name"] = candidate_name
        data["job_title"] = job_title
        data["analyzed_at"] = datetime.now(tz=timezone.utc).isoformat()

        try:
            gap_result = SkillGapResult.model_validate(data)
        except PydanticValidationError as exc:
            logger.warning(
                "Pydantic validation failed: %d errors | candidate=%s",
                exc.error_count(),
                candidate_name,
            )
            raise ValidationError(
                pydantic_errors=exc.errors(include_url=False)
            ) from exc

        return gap_result

"""
JobAgent — the Job Intelligence Agent.

This is the APPLICATION LAYER orchestrator for job descriptions. It coordinates:
  1. Prompt building (via JobExtractionPrompt)
  2. LLM invocation (via LLMProvider interface)
  3. JSON extraction + Pydantic validation
  4. Result wrapping (via AgentResult monad)

DESIGN INVARIANTS:
- The agent depends ONLY on abstractions (LLMProvider).
- The agent NEVER raises exceptions to the caller — it returns AgentResult.
- Focuses strictly on extraction and normalization. Does NOT score or match candidates.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from core.exceptions import (
    EmptyDocumentError,
    ExtractionError,
    ParseError,
    ProviderError,
    RecruitmentError,
    ValidationError,
)
from core.result import AgentResult
from models.job_description import JobDescription
from prompts.job_prompt import JobExtractionPrompt
from providers.base import GenerationConfig, LLMProvider

logger = logging.getLogger(__name__)


class JobAgent:
    """
    Job Intelligence Agent.

    Transforms unstructured job description text into a validated JobDescription
    domain object via LLM-powered structured extraction.
    """

    def __init__(
        self,
        provider: LLMProvider,
        prompt: JobExtractionPrompt | None = None,
        generation_config: GenerationConfig | None = None,
        min_job_words: int = 20,
    ) -> None:
        """
        Dependency-injected constructor.

        Args:
            provider: Any LLMProvider implementation.
            prompt: Override for custom/experimental prompts.
            generation_config: Override LLM generation parameters.
            min_job_words: Minimum word count to accept a job description.
        """
        self._provider = provider
        self._prompt = prompt or JobExtractionPrompt()
        self._generation_config = generation_config or GenerationConfig(
            temperature=0.1,
            max_output_tokens=4096,
            response_format="json",
        )
        self._min_job_words = min_job_words

        logger.info(
            "JobAgent initialized | provider=%s | prompt_version=%s",
            provider.get_model_name(),
            self._prompt.version,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def process_text(self, job_text: str, source_name: str = "inline") -> AgentResult[JobDescription]:
        """
        Process a job description from raw text.

        The pipeline is:
            Build prompt → Call LLM → Extract JSON → Validate

        Args:
            job_text: The raw text content of the job description.
            source_name: Logical name for traceability.

        Returns:
            AgentResult.success(JobDescription) on success.
            AgentResult.failure(RecruitmentError) on any failure.
        """
        logger.info("Processing job description from text: source='%s'", source_name)

        try:
            if not job_text or not job_text.strip():
                raise EmptyDocumentError(source_name)

            if len(job_text.split()) < self._min_job_words:
                raise EmptyDocumentError(source_name)

            # ── Stage 1: Build prompt ─────────────────────────────────────
            prompt_str = self._build_prompt(job_text)

            # ── Stage 2: Call LLM ─────────────────────────────────────────
            response = self._call_provider(prompt_str)

            # ── Stage 3: Extract JSON ──────────────────────────────────────
            data = self._extract_json(response.content)

            # ── Stage 4: Validate with Pydantic ──────────────────────────
            job_desc = self._validate(data=data, source_name=source_name)

            logger.info(
                "Job description processed successfully: '%s' | summary=%s",
                source_name,
                job_desc.summary_dict(),
            )
            return AgentResult.success(
                value=job_desc,
                metadata={
                    "source_name": source_name,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "prompt_version": self._prompt.version,
                },
            )

        except RecruitmentError as exc:
            logger.warning("JobAgent pipeline error: %s", exc)
            return AgentResult.failure(error=exc, metadata={"source_name": source_name})

        except Exception as exc:
            logger.exception("Unexpected error in JobAgent: %s", exc)
            wrapped = RecruitmentError(
                message=f"Unexpected agent error: {exc}",
                details={"exception_type": type(exc).__name__},
            )
            return AgentResult.failure(error=wrapped, metadata={"source_name": source_name})

    # ── Private pipeline stages ───────────────────────────────────────────────

    def _build_prompt(self, job_text: str) -> str:
        """Stage 1: Render the extraction prompt."""
        return self._prompt.build(job_text=job_text)

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

        if data.get("error") == "Not a job description":
            raise ParseError(
                message="The text does not appear to be a job description.",
                details={"llm_flag": data.get("error")},
            )

        return data

    def _validate(self, data: dict[str, Any], source_name: str) -> JobDescription:
        """
        Stage 4: Validate extracted dict against the JobDescription schema.
        """
        data["source_name"] = source_name
        data["extracted_at"] = datetime.now(tz=timezone.utc).isoformat()

        try:
            job_desc = JobDescription.model_validate(data)
        except PydanticValidationError as exc:
            logger.warning(
                "Pydantic validation failed: %d errors | source=%s",
                exc.error_count(),
                source_name,
            )
            raise ValidationError(
                pydantic_errors=exc.errors(include_url=False)
            ) from exc

        return job_desc

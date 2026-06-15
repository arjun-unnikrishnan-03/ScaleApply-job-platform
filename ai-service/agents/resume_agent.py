"""
ResumeAgent — the Resume Intelligence Agent.

This is the APPLICATION LAYER orchestrator. It coordinates:
  1. File parsing (via ResumeParserFactory)
  2. Prompt building (via ResumeExtractionPrompt)
  3. LLM invocation (via LLMProvider interface)
  4. JSON extraction + Pydantic validation
  5. Result wrapping (via AgentResult monad)

DESIGN INVARIANTS:
- The agent depends ONLY on abstractions (LLMProvider, ResumeParserFactory).
- The agent has NO imports from google, openai, or any SDK.
- The agent NEVER raises exceptions to the caller — it returns AgentResult.
- All I/O (file reads, API calls) is delegated to injected dependencies.

Usage:
    provider = ProviderFactory.create("gemini", api_key="...")
    agent = ResumeAgent(provider=provider)
    result = agent.process(Path("resume.pdf"))

    if result.is_success:
        profile = result.value  # CandidateProfile
    else:
        print(result.error)     # RecruitmentError subclass
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from agents.text_processor import TextProcessor
from core.exceptions import (
    EmptyDocumentError,
    ExtractionError,
    ParseError,
    ProviderError,
    RecruitmentError,
    ValidationError,
)
from core.result import AgentResult
from models.candidate_profile import CandidateProfile
from parsers.factory import ResumeParserFactory
from prompts.resume_prompt import ResumeExtractionPrompt
from providers.base import GenerationConfig, LLMProvider

logger = logging.getLogger(__name__)


class ResumeAgent:
    """
    Resume Intelligence Agent.

    Transforms a raw resume file into a validated CandidateProfile
    domain object via LLM-powered structured extraction.

    Future agents (ATS, Skill Gap, Interview, Recruiter) will accept
    CandidateProfile as their primary input, making this agent the
    universal entry point of the AI recruitment pipeline.
    """

    def __init__(
        self,
        provider: LLMProvider,
        parser_factory: type[ResumeParserFactory] | None = None,
        prompt: ResumeExtractionPrompt | None = None,
        generation_config: GenerationConfig | None = None,
        min_resume_words: int = 30,
    ) -> None:
        """
        Dependency-injected constructor.

        Args:
            provider: Any LLMProvider implementation (Gemini, OpenAI, etc.)
            parser_factory: Override for custom parser registry (useful in tests).
            prompt: Override for custom/experimental prompts (useful in A/B tests).
            generation_config: Override LLM generation parameters.
            min_resume_words: Minimum word count to accept a parsed document.
        """
        self._provider = provider
        self._parser_factory = parser_factory or ResumeParserFactory
        self._prompt = prompt or ResumeExtractionPrompt()
        self._generation_config = generation_config or GenerationConfig(
            temperature=0.1,         # Low creativity for factual extraction
            max_output_tokens=4096,
            response_format="json",
        )
        self._min_resume_words = min_resume_words

        logger.info(
            "ResumeAgent initialized | provider=%s | prompt_version=%s",
            provider.get_model_name(),
            self._prompt.version,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def process(self, file_path: Path | str) -> AgentResult[CandidateProfile]:
        """
        Full pipeline: file → CandidateProfile.

        The pipeline is:
            Parse file → Build prompt → Call LLM → Extract JSON → Validate

        Returns:
            AgentResult.success(CandidateProfile) on success.
            AgentResult.failure(RecruitmentError) on any failure.

        Never raises — all exceptions are caught and wrapped.
        """
        path = Path(file_path)
        logger.info("Processing resume: '%s'", path.name)

        try:
            # ── Stage 1: Parse file ───────────────────────────────────────
            parsed_doc = self._parse_file(path)

            # ── Stage 2: Build prompt ─────────────────────────────────────
            prompt_str = self._build_prompt(parsed_doc.raw_text)

            # ── Stage 3: Call LLM ─────────────────────────────────────────
            response = self._call_provider(prompt_str)

            # ── Stage 4: Extract JSON ──────────────────────────────────────
            data = self._extract_json(response.content)

            # ── Stage 5: Validate with Pydantic ──────────────────────────
            profile = self._validate(
                data=data,
                source_file=path.name,
            )

            logger.info(
                "Resume processed successfully: '%s' | summary=%s",
                path.name,
                profile.summary_dict(),
            )
            return AgentResult.success(
                value=profile,
                metadata={
                    "source_file": path.name,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "prompt_version": self._prompt.version,
                    "word_count": parsed_doc.word_count,
                },
            )

        except RecruitmentError as exc:
            logger.warning("ResumeAgent pipeline error: %s", exc)
            return AgentResult.failure(error=exc, metadata={"source_file": str(path)})

        except Exception as exc:
            # Catch unexpected errors and wrap them as domain errors
            logger.exception("Unexpected error in ResumeAgent: %s", exc)
            wrapped = RecruitmentError(
                message=f"Unexpected agent error: {exc}",
                details={"exception_type": type(exc).__name__},
            )
            return AgentResult.failure(error=wrapped, metadata={"source_file": str(path)})

    def process_text(self, resume_text: str, source_name: str = "inline") -> AgentResult[CandidateProfile]:
        """
        Process a resume from raw text (bypasses file parsing).

        Useful for:
        - Unit testing without real files
        - Processing resumes already fetched from a database or S3
        - Future RAG pipeline ingestion

        Args:
            resume_text: The raw text content of the resume.
            source_name: Logical name for traceability (e.g. 's3://bucket/key.pdf').
        """
        logger.info("Processing resume from text: source='%s'", source_name)

        try:
            if not resume_text or not resume_text.strip():
                raise EmptyDocumentError(source_name)

            if len(resume_text.split()) < self._min_resume_words:
                raise EmptyDocumentError(source_name)

            prompt_str = self._build_prompt(resume_text)
            response = self._call_provider(prompt_str)
            data = self._extract_json(response.content)
            profile = self._validate(data=data, source_file=source_name)

            return AgentResult.success(
                value=profile,
                metadata={
                    "source_file": source_name,
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "prompt_version": self._prompt.version,
                },
            )

        except RecruitmentError as exc:
            logger.warning("ResumeAgent text-mode error: %s", exc)
            return AgentResult.failure(error=exc, metadata={"source_file": source_name})

        except Exception as exc:
            logger.exception("Unexpected error in process_text: %s", exc)
            wrapped = RecruitmentError(
                message=f"Unexpected agent error: {exc}",
                details={"exception_type": type(exc).__name__},
            )
            return AgentResult.failure(error=wrapped)

    # ── Private pipeline stages ───────────────────────────────────────────────

    def _parse_file(self, path: Path):
        """Stage 1: Dispatch to the appropriate parser."""
        parser = self._parser_factory.get_parser(path)
        doc = parser.parse(path)

        if not doc.is_usable(min_words=self._min_resume_words):
            raise EmptyDocumentError(str(path))

        logger.debug(
            "File parsed: format=%s | words=%d | pages=%d",
            doc.file_format,
            doc.word_count,
            doc.page_count,
        )
        return doc

    def _build_prompt(self, resume_text: str) -> str:
        """Stage 2: Render the extraction prompt."""
        return self._prompt.build(resume_text=resume_text)

    def _call_provider(self, prompt: str):
        """Stage 3: Invoke the LLM via the provider interface."""
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
            raise  # Already a domain error, propagate as-is
        except Exception as exc:
            raise ProviderError(f"Provider call failed: {exc}") from exc

    def _extract_json(self, raw_content: str) -> dict[str, Any]:
        """
        Stage 4: Extract a JSON dict from the LLM response.

        Handles:
        - Clean JSON responses
        - JSON wrapped in markdown code fences (```json ... ```)
        - JSON embedded mid-text with surrounding noise
        """
        if not raw_content:
            raise ExtractionError(raw_content or "")

        content = raw_content.strip()

        # Strip markdown code fences if present
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
        content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
        content = content.strip()

        # Find the outermost JSON object
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

        # Check if the LLM flagged the document as not a resume
        if data.get("error") == "Not a resume":
            raise ParseError(
                message="The document does not appear to be a resume.",
                details={"llm_flag": data.get("error")},
            )

        return data

    def _validate(self, data: dict[str, Any], source_file: str) -> CandidateProfile:
        """
        Stage 5: Validate extracted dict against the CandidateProfile schema.

        Injects agent-level metadata (source_file, extracted_at) before
        validation so the domain object is self-documenting.
        """
        # Inject traceability fields
        data["source_file"] = source_file
        data["extracted_at"] = datetime.now(tz=timezone.utc).isoformat()

        try:
            profile = CandidateProfile.model_validate(data)
        except PydanticValidationError as exc:
            logger.warning(
                "Pydantic validation failed: %d errors | source=%s",
                exc.error_count(),
                source_file,
            )
            raise ValidationError(
                pydantic_errors=exc.errors(include_url=False)
            ) from exc

        return profile

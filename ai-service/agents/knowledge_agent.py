"""
KnowledgeAgent — the RAG-enabled intelligence agent.

This is the APPLICATION LAYER orchestrator for querying the knowledge base.
It coordinates:
  1. Retrieval (via RetrievalService)
  2. Prompt building (via KnowledgePrompt)
  3. LLM invocation (via LLMProvider interface)
  4. JSON extraction + Pydantic validation
  5. Result wrapping (via AgentResult monad)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from core.exceptions import (
    ExtractionError,
    ProviderError,
    RecruitmentError,
    ValidationError,
)
from core.result import AgentResult
from models.knowledge_response import KnowledgeResponse
from prompts.knowledge_prompt import KnowledgePrompt
from providers.base import GenerationConfig, LLMProvider
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """
    RAG-enabled Knowledge Agent.

    Synthesizes answers to natural language questions based purely on 
    retrieved documents from the vector store.
    """

    def __init__(
        self,
        provider: LLMProvider,
        retrieval_service: RetrievalService,
        prompt: KnowledgePrompt | None = None,
        generation_config: GenerationConfig | None = None,
    ) -> None:
        """
        Dependency-injected constructor.

        Args:
            provider: Any LLMProvider implementation.
            retrieval_service: Service responsible for fetching context documents.
            prompt: Override for custom/experimental prompts.
            generation_config: Override LLM generation parameters.
        """
        self._provider = provider
        self._retrieval_service = retrieval_service
        self._prompt = prompt or KnowledgePrompt()
        self._generation_config = generation_config or GenerationConfig(
            temperature=0.0,  # Zero temperature for strict factual adherence
            max_output_tokens=1024,
            response_format="json",
        )

        logger.info(
            "KnowledgeAgent initialized | provider=%s | prompt_version=%s",
            provider.get_model_name(),
            self._prompt.version,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str) -> AgentResult[KnowledgeResponse]:
        """
        Answer a question using the Retrieval-Augmented Generation pipeline.

        The pipeline is:
            Retrieve Context → Build prompt → Call LLM → Extract JSON → Validate

        Args:
            question: Natural language query.

        Returns:
            AgentResult.success(KnowledgeResponse) on success.
            AgentResult.failure(RecruitmentError) on any failure.
        """
        logger.info("KnowledgeAgent processing question: '%s'", question)

        try:
            # ── Stage 1: Retrieve context ─────────────────────────────────
            retrieval_res = self._retrieval_service.retrieve(question)
            if not retrieval_res.is_success:
                logger.error("Retrieval failed: %s", retrieval_res.error)
                return AgentResult.failure(error=retrieval_res.error) # type: ignore
                
            retrieval_result = retrieval_res.unwrap()

            # ── Stage 2: Build prompt ─────────────────────────────────────
            prompt_str = self._build_prompt(retrieval_result)

            # ── Stage 3: Call LLM ─────────────────────────────────────────
            response = self._call_provider(prompt_str)

            # ── Stage 4: Extract JSON ──────────────────────────────────────
            data = self._extract_json(response.content)

            # ── Stage 5: Validate with Pydantic ──────────────────────────
            knowledge_response = self._validate(data=data)

            logger.info(
                "Knowledge response generated: confidence=%.2f | sources=%d",
                knowledge_response.confidence,
                len(knowledge_response.sources),
            )
            return AgentResult.success(
                value=knowledge_response,
                metadata={
                    "model": response.model,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "prompt_version": self._prompt.version,
                    "retrieved_documents": len(retrieval_result.documents)
                },
            )

        except RecruitmentError as exc:
            logger.warning("KnowledgeAgent pipeline error: %s", exc)
            return AgentResult.failure(error=exc)

        except Exception as exc:
            logger.exception("Unexpected error in KnowledgeAgent: %s", exc)
            wrapped = RecruitmentError(
                message=f"Unexpected agent error: {exc}",
                details={"exception_type": type(exc).__name__},
            )
            return AgentResult.failure(error=wrapped)

    # ── Private pipeline stages ───────────────────────────────────────────────

    def _build_prompt(self, retrieval_result: Any) -> str:
        """Stage 2: Render the RAG prompt."""
        return self._prompt.build(retrieval_result=retrieval_result)

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
            raise
        except Exception as exc:
            raise ProviderError(f"Provider call failed: {exc}") from exc

    def _extract_json(self, raw_content: str) -> dict[str, Any]:
        """Stage 4: Extract a JSON dict from the LLM response."""
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

    def _validate(self, data: dict[str, Any]) -> KnowledgeResponse:
        """Stage 5: Validate extracted dict against the schema."""
        try:
            response = KnowledgeResponse.model_validate(data)
        except PydanticValidationError as exc:
            logger.warning("Pydantic validation failed: %d errors", exc.error_count())
            raise ValidationError(
                pydantic_errors=exc.errors(include_url=False)
            ) from exc

        return response

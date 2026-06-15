"""
Gemini implementation of the LLMProvider.
"""

from __future__ import annotations

import logging
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from core.exceptions import (
    GeminiAuthenticationError,
    GeminiProviderError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    ProviderResponseError,
)
from providers.base import GenerationConfig, LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)


def _is_retryable_exception(exc: BaseException) -> bool:
    """Return True if the exception should trigger a retry."""
    return isinstance(
        exc,
        (
            google_exceptions.ResourceExhausted,
            google_exceptions.InternalServerError,
            google_exceptions.ServiceUnavailable,
            google_exceptions.GatewayTimeout,
        ),
    )


class GeminiProvider(LLMProvider):
    """
    Production-ready Gemini LLM Provider utilizing the official google-generativeai SDK.
    Includes exponential backoff retries and structured logging.
    """

    def __init__(self, api_key: str | None = None, model_name: str | None = None, model: str | None = None) -> None:
        """
        Initialize the Gemini provider.

        Args:
            api_key: The API key. If not provided, reads from settings.gemini_api_key or settings.llm_api_key.
            model_name: The model to use. Defaults to settings.gemini_model.
            model: Alias for model_name for factory compatibility.
        """
        self.api_key = api_key or settings.gemini_api_key or settings.llm_api_key
        self.model_name = model or model_name or settings.gemini_model

        if not self.api_key:
            raise GeminiAuthenticationError("Gemini API key is not configured.")

        # Configure the global genai client
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info("Initialized GeminiProvider targeted at model '%s'", self.model_name)

    def get_model_name(self) -> str:
        """Return the identifier of the configured model."""
        return self.model_name

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> ProviderResponse:
        """
        Send a prompt to the Gemini API and return the formatted response.

        Args:
            prompt: The string prompt.
            config: Optional generation parameters.

        Returns:
            ProviderResponse containing the output and usage metrics.
            
        Raises:
            GeminiAuthenticationError: On 403 or invalid API key.
            GeminiRateLimitError: If retries are exhausted on 429 errors.
            GeminiTimeoutError: On request timeout.
            GeminiProviderError: For all other SDK errors.
        """
        if not prompt or not prompt.strip():
            raise ProviderResponseError("Cannot generate response for empty prompt.")

        cfg = config or GenerationConfig()
        
        # Build the SDK specific generation config
        generation_config = genai.types.GenerationConfig(
            temperature=cfg.temperature,
            max_output_tokens=cfg.max_output_tokens,
            response_mime_type="application/json" if cfg.response_format == "json" else "text/plain",
        )

        try:
            return self._execute_with_retry(prompt, generation_config)
        except google_exceptions.PermissionDenied as exc:
            logger.error("Gemini Authentication failed.")
            raise GeminiAuthenticationError("Invalid or unauthorized API key.") from exc
        except google_exceptions.ResourceExhausted as exc:
            logger.error("Gemini Rate Limit Exhausted after retries.")
            raise GeminiRateLimitError("Quota exceeded or rate limit reached.") from exc
        except google_exceptions.GatewayTimeout as exc:
            logger.error("Gemini API request timed out.")
            raise GeminiTimeoutError("API request timed out.") from exc
        except google_exceptions.GoogleAPIError as exc:
            logger.error("Gemini API returned an error: %s", exc)
            raise GeminiProviderError(f"SDK Error: {exc}") from exc
        except ProviderResponseError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error in GeminiProvider: %s", exc)
            raise GeminiProviderError(f"Unexpected error: {exc}") from exc

    # Tenacity is configured using settings values inside the decorator.
    # To use dynamic settings at instantiation, we apply tenacity programmatically
    # or rely on the class structure. Using decorator with getters is cleanest.
    @retry(
        retry=retry_if_exception_type((
            google_exceptions.ResourceExhausted,
            google_exceptions.InternalServerError,
            google_exceptions.ServiceUnavailable,
            google_exceptions.GatewayTimeout,
        )),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(settings.gemini_max_retries),
        reraise=True
    )
    def _execute_with_retry(
        self, prompt: str, generation_config: genai.types.GenerationConfig
    ) -> ProviderResponse:
        """Execute the SDK call with tenacity retry policies."""
        logger.debug("Sending generation request to Gemini (model=%s, length=%d)", self.model_name, len(prompt))
        
        start_time = time.perf_counter()
        
        # Make the API call
        # The timeout is handled inside the transport layer typically, but we configure it via the SDK if supported,
        # or rely on the requests layer. Currently, standard SDK usage is sufficient.
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
        
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            request_options={"timeout": settings.gemini_timeout_seconds}
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        if response.candidates:
            candidate = response.candidates[0]
            logger.info("Gemini Candidate finish reason: %s", candidate.finish_reason)
            if hasattr(candidate, "safety_ratings") and candidate.safety_ratings:
                logger.info("Gemini Safety ratings: %s", [dict(category=r.category, probability=r.probability, blocked=r.blocked) for r in candidate.safety_ratings])

        if not response or not response.text:
            raise ProviderResponseError("Gemini API returned an empty response.")

        # Extract usage metadata if available
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        logger.info(
            "Gemini generation successful. Latency: %.2fms, Input Tokens: %d, Output Tokens: %d",
            latency_ms,
            input_tokens,
            output_tokens
        )

        return ProviderResponse(
            content=response.text,
            model=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            raw_metadata={"latency_ms": latency_ms},
        )

    def health_check(self) -> bool:
        """
        Perform a minimal connectivity check.
        Returns True if the provider is reachable and configured.
        """
        try:
            # A simple way to check is to try fetching the model info.
            # Using list_models or get_model is lightweight.
            genai.get_model(f"models/{self.model_name}")
            return True
        except Exception as exc:
            logger.warning("Gemini health check failed: %s", exc)
            return False

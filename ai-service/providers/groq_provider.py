"""
Groq implementation of the LLMProvider.
"""

from __future__ import annotations

import logging
import time

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from core.exceptions import (
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from providers.base import GenerationConfig, LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    """
    Groq LLM Provider utilizing the OpenAI-compatible REST API via requests.
    """

    def __init__(self, api_key: str | None = None, model_name: str | None = None, model: str | None = None) -> None:
        """
        Initialize the Groq provider.
        """
        self.api_key = api_key or getattr(settings, "groq_api_key", None) or settings.llm_api_key
        self.model_name = model or model_name or getattr(settings, "groq_model", "llama3-70b-8192")

        if not self.api_key:
            raise ProviderAuthError("Groq API key is not configured.")

        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        logger.info("Initialized GroqProvider targeted at model '%s'", self.model_name)

    def get_model_name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> ProviderResponse:
        """
        Send a prompt to the Groq API and return the formatted response.
        """
        if not prompt or not prompt.strip():
            raise ProviderResponseError("Cannot generate response for empty prompt.")

        cfg = config or GenerationConfig()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_output_tokens,
            "top_p": cfg.top_p
        }
        if cfg.response_format == "json":
            # Groq requires the prompt to mention "JSON" if json_object is used
            if "json" not in prompt.lower():
                payload["messages"][0]["content"] += "\n\nPlease return a valid JSON object."
            payload["response_format"] = {"type": "json_object"}

        try:
            return self._execute_with_retry(headers, payload)
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code
            error_text = exc.response.text
            if status_code in (401, 403):
                raise ProviderAuthError(f"Groq Authentication failed: {exc} - {error_text}") from exc
            if status_code == 429:
                raise ProviderRateLimitError(f"Groq Rate limit exceeded: {exc} - {error_text}") from exc
            raise ProviderError(f"Groq API HTTP error {status_code}: {exc} - {error_text}") from exc
        except ProviderResponseError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error in GroqProvider: %s", exc)
            raise ProviderError(f"Unexpected error: {exc}") from exc

    @retry(
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def _execute_with_retry(self, headers: dict, payload: dict) -> ProviderResponse:
        start_time = time.perf_counter()
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        data = response.json()
        
        if not data.get("choices"):
            raise ProviderResponseError("Groq API returned an empty or invalid response.")
            
        choice = data["choices"][0]
        content = choice.get("message", {}).get("content", "")
        finish_reason = choice.get("finish_reason", "stop")
        
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        logger.info(
            "Groq generation successful. Latency: %.2fms, Input Tokens: %d, Output Tokens: %d",
            latency_ms,
            input_tokens,
            output_tokens
        )

        return ProviderResponse(
            content=content,
            model=self.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
            raw_metadata={"latency_ms": latency_ms},
        )

    def health_check(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

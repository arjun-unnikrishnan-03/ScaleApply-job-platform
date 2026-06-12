"""
LLM Provider abstraction layer.

All concrete LLM implementations MUST implement LLMProvider.
The ResumeAgent only ever interacts with this interface —
making the system provider-agnostic by design.

Adding a new provider (OpenAI, Claude, Mistral, local Ollama):
1. Create a new file in providers/
2. Subclass LLMProvider
3. Register in providers/factory.py

Zero changes to agents required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderResponse:
    """
    Standardized response envelope from any LLM provider.

    Wraps the raw text alongside usage metadata so callers can
    monitor token costs without depending on provider-specific objects.
    """

    content: str                         # The generated text
    model: str                           # Which model variant was used
    input_tokens: int = 0                # Prompt token count (if available)
    output_tokens: int = 0               # Completion token count (if available)
    finish_reason: str = "stop"          # 'stop', 'max_tokens', 'error', etc.
    raw_metadata: dict = field(default_factory=dict)  # Provider-specific extras

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def is_complete(self) -> bool:
        """Returns True if the generation completed normally."""
        return self.finish_reason in {"stop", "end_turn", "complete"}


@dataclass(frozen=True)
class GenerationConfig:
    """
    Provider-agnostic generation hyperparameters.

    Each provider's `generate()` implementation is responsible
    for mapping these to its own SDK's parameter names.
    """

    temperature: float = 0.1        # Low temp for structured extraction
    max_output_tokens: int = 4096
    top_p: float = 0.95
    response_format: str = "json"   # Hint: prefer JSON mode when available


class LLMProvider(ABC):
    """
    Abstract interface that every LLM provider must implement.

    Dependency inversion principle: high-level modules (agents)
    depend on this abstraction, not on concrete implementations.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: GenerationConfig | None = None,
    ) -> ProviderResponse:
        """
        Send a prompt to the LLM and return a normalized response.

        Args:
            prompt: The fully-rendered prompt string.
            config: Optional generation configuration overrides.

        Returns:
            ProviderResponse with the generated content.

        Raises:
            ProviderError: On any API-level failure.
            ProviderAuthError: On authentication failures.
            ProviderRateLimitError: On rate-limit responses.
        """

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the canonical model identifier string."""

    @abstractmethod
    def health_check(self) -> bool:
        """
        Perform a minimal connectivity check.
        Returns True if the provider is reachable and configured.
        """

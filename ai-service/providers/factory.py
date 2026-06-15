"""
ProviderFactory — Registry pattern for LLM provider creation.

Usage:
    # Simple creation
    provider = ProviderFactory.create("gemini", api_key="...")

    # From environment / config object
    provider = ProviderFactory.from_settings(settings)

Adding a new provider (e.g. OpenAI):
    1. Create providers/openai_provider.py implementing LLMProvider
    2. Add one line: ProviderFactory.register("openai", OpenAIProvider)
    3. Done — no other files need to change.
"""

from __future__ import annotations

import logging
from typing import ClassVar, Type

from providers.base import LLMProvider
from core.exceptions import ProviderNotFoundError

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Registry-based factory for LLM providers.

    The registry maps lowercase provider names to their classes.
    Construction kwargs are forwarded directly to the provider's __init__.
    """

    # Registry: name → provider class
    _registry: ClassVar[dict[str, Type[LLMProvider]]] = {}

    # ── Registration ──────────────────────────────────────────────────────

    @classmethod
    def register(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """
        Register a new provider class under a name.

        This is called at module load time (see bottom of this file)
        and can be called by external code to add custom providers.
        """
        normalized = name.lower().strip()
        cls._registry[normalized] = provider_class
        logger.debug("Provider registered: '%s' → %s", normalized, provider_class.__name__)

    @classmethod
    def available_providers(cls) -> list[str]:
        """Return all registered provider names."""
        return sorted(cls._registry.keys())

    # ── Factory methods ───────────────────────────────────────────────────

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> LLMProvider:
        """
        Instantiate a provider by name, passing kwargs to its constructor.

        Args:
            provider_name: One of the registered names (case-insensitive).
            **kwargs: Provider-specific constructor arguments
                      (e.g., api_key="...", model="...").

        Returns:
            A fully configured LLMProvider instance.

        Raises:
            ProviderNotFoundError: If the name is not registered.
            ProviderAuthError: If required credentials are missing.

        Examples:
            provider = ProviderFactory.create("gemini", api_key="AIza...")
            provider = ProviderFactory.create("openai", api_key="sk-...", model="gpt-4o")
            provider = ProviderFactory.create("claude", api_key="sk-ant-...")
            provider = ProviderFactory.create("ollama", base_url="http://localhost:11434", model="llama3")
        """
        name = provider_name.lower().strip()
        if name not in cls._registry:
            raise ProviderNotFoundError(
                provider_name=name,
                available=cls.available_providers(),
            )
        provider_class = cls._registry[name]
        logger.info("Creating provider: '%s' using %s", name, provider_class.__name__)
        return provider_class(**kwargs)

    @classmethod
    def from_settings(cls, settings) -> LLMProvider:
        """
        Create a provider from a settings/config object.

        The settings object must have:
            - settings.llm_provider: str  (provider name)
            - settings.llm_api_key: str
            - settings.llm_model: str (optional)

        This method allows the entire provider selection to be
        controlled by environment variables with zero code changes.
        """
        kwargs: dict = {"api_key": settings.llm_api_key}
        if hasattr(settings, "llm_model") and settings.llm_model:
            kwargs["model"] = settings.llm_model
        return cls.create(settings.llm_provider, **kwargs)


# ── Auto-register built-in providers ─────────────────────────────────────────
# Import here to avoid circular imports. These registrations happen once
# at module load time.

def _register_builtin_providers() -> None:
    """
    Register all bundled providers.

    Future providers (OpenAI, Claude, Ollama) will be added here.
    Each registration is guarded so that missing optional dependencies
    don't crash the factory if that provider isn't installed.
    """
    # Gemini (always available if google-generativeai is installed)
    try:
        from providers.gemini_provider import GeminiProvider
        ProviderFactory.register("gemini", GeminiProvider)
    except ImportError:
        logger.warning("GeminiProvider not registered — google-generativeai not installed.")

    # ── Future providers (uncomment when implemented) ─────────────────────
    # from providers.openai_provider import OpenAIProvider
    # ProviderFactory.register("openai", OpenAIProvider)
    #
    # from providers.claude_provider import ClaudeProvider
    # ProviderFactory.register("claude", ClaudeProvider)
    #
    # from providers.ollama_provider import OllamaProvider
    # ProviderFactory.register("ollama", OllamaProvider)


_register_builtin_providers()

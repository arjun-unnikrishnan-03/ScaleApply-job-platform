"""
Provider dependency injection — resolves LLM provider from settings.
"""
from __future__ import annotations

from functools import lru_cache

from config.settings import settings
from providers.base import LLMProvider
from providers.factory import ProviderFactory


@lru_cache(maxsize=1)
def _create_llm_provider() -> LLMProvider:
    """Create and cache the LLM provider singleton."""
    return ProviderFactory.from_settings(settings)


def get_llm_provider() -> LLMProvider:
    """
    FastAPI dependency that resolves the configured LLM provider.
    Cached globally — provider is created only once per application lifecycle.
    """
    return _create_llm_provider()

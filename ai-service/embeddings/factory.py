"""
Factory for creating EmbeddingProviders.
"""

from __future__ import annotations

from typing import Any, Callable

from embeddings.base import EmbeddingProvider
from embeddings.gemini_embeddings import GeminiEmbeddingProvider


class EmbeddingFactory:
    """
    Factory class to instantiate EmbeddingProviders dynamically.
    """

    _registry: dict[str, type[EmbeddingProvider] | Callable[..., EmbeddingProvider]] = {
        "gemini": GeminiEmbeddingProvider,
    }

    @classmethod
    def register(cls, name: str, provider_class: type[EmbeddingProvider] | Callable[..., EmbeddingProvider]) -> None:
        """Register a new provider class."""
        cls._registry[name.lower()] = provider_class

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> EmbeddingProvider:
        """
        Create an EmbeddingProvider instance by name.
        """
        key = name.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown embedding provider: {name}. Available: {list(cls._registry.keys())}")
        
        provider_class = cls._registry[key]
        return provider_class(**kwargs)

    @classmethod
    def available_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._registry.keys())

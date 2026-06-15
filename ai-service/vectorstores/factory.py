"""
Factory for creating VectorStores.
"""

from __future__ import annotations

from typing import Any, Callable

from vectorstores.base import VectorStore
from vectorstores.qdrant_store import QdrantVectorStore


class VectorStoreFactory:
    """
    Factory class to instantiate VectorStores dynamically.
    """

    _registry: dict[str, type[VectorStore] | Callable[..., VectorStore]] = {
        "qdrant": QdrantVectorStore,
    }

    @classmethod
    def register(cls, name: str, store_class: type[VectorStore] | Callable[..., VectorStore]) -> None:
        """Register a new vector store class."""
        cls._registry[name.lower()] = store_class

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> VectorStore:
        """
        Create a VectorStore instance by name.
        """
        key = name.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown vector store: {name}. Available: {list(cls._registry.keys())}")
        
        store_class = cls._registry[key]
        return store_class(**kwargs)

    @classmethod
    def available_stores(cls) -> list[str]:
        """List all registered vector stores."""
        return list(cls._registry.keys())

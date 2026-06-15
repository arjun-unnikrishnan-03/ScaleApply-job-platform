"""
VectorStore dependency injection — resolves embedding provider and vector store from settings.
"""
from __future__ import annotations

from functools import lru_cache

from config.settings import settings
from embeddings.base import EmbeddingProvider
from embeddings.factory import EmbeddingFactory
from vectorstores.base import VectorStore
from vectorstores.qdrant_store import QdrantVectorStore


@lru_cache(maxsize=1)
def _create_embedding_provider() -> EmbeddingProvider:
    """Create and cache the embedding provider singleton."""
    return EmbeddingFactory.create(
        "gemini",
        api_key=settings.gemini_api_key or settings.llm_api_key,
        model_name=settings.embedding_model,
    )


@lru_cache(maxsize=1)
def _create_vector_store() -> VectorStore:
    """Create and cache the Qdrant vector store singleton."""
    return QdrantVectorStore()


def get_embedding_provider() -> EmbeddingProvider:
    """FastAPI dependency resolving the embedding provider."""
    return _create_embedding_provider()


def get_vector_store() -> VectorStore:
    """FastAPI dependency resolving the vector store."""
    return _create_vector_store()

"""
RetrievalService — orchestrates generating vectors for queries and fetching documents.
"""

from __future__ import annotations

import logging

from core.result import AgentResult
from core.exceptions import ProviderError
from embeddings.base import EmbeddingProvider
from vectorstores.base import VectorStore
from models.retrieval_result import RetrievalResult
from models.knowledge_chunk import KnowledgeChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service responsible for converting natural language queries into 
    embeddings and performing vector similarity search.
    """

    def __init__(self, provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        """
        Initialize with injected dependencies.

        Args:
            provider: The embedding provider (e.g., Gemini).
            vector_store: The destination vector database (e.g., Qdrant).
        """
        self._provider = provider
        self._vector_store = vector_store
        logger.info("RetrievalService initialized")

    def retrieve(self, query: str, limit: int = 3) -> AgentResult[RetrievalResult]:
        """
        Embed the query and retrieve relevant documents from the vector store.

        Args:
            query: The natural language search query.
            limit: Maximum number of documents to retrieve.

        Returns:
            AgentResult.success(RetrievalResult) on success.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to RetrievalService.")
            return AgentResult.success(RetrievalResult(query="", documents=[], scores=[]))

        logger.info("Retrieving knowledge for query: '%s'", query)

        try:
            # 1. Generate the embedding vector for the query
            query_vector = self._provider.embed_text(query)

            # 2. Search the vector store
            documents = self._vector_store.search(query_vector=query_vector, limit=limit)
            
            # Since the VectorStore abstraction doesn't currently return scores,
            # we stub them out to 1.0. A real implementation would return distances.
            scores = [1.0 for _ in documents]

            logger.info("Retrieved %d documents for query '%s'", len(documents), query)
            
            result = RetrievalResult(
                query=query,
                documents=documents,
                scores=scores
            )
            
            return AgentResult.success(
                value=result,
                metadata={
                    "retrieved_count": len(documents),
                    "query_length": len(query)
                }
            )

        except ProviderError as exc:
            logger.error("Query embedding generation failed: %s", exc)
            return AgentResult.failure(error=exc)
        except Exception as exc:
            logger.exception("Unexpected error during retrieval: %s", exc)
            wrapped_err = RuntimeError(f"Unexpected retrieval error: {exc}")
            return AgentResult.failure(error=wrapped_err)

    def retrieve_chunks(self, query: str, limit: int = 3) -> AgentResult[list[KnowledgeChunk]]:
        """
        Embed the query and retrieve relevant chunks from the vector store.

        Args:
            query: The natural language search query.
            limit: Maximum number of chunks to retrieve.

        Returns:
            AgentResult.success(list[KnowledgeChunk]) on success.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to RetrievalService.")
            return AgentResult.success([])

        logger.info("Retrieving knowledge chunks for query: '%s'", query)

        try:
            # 1. Generate the embedding vector for the query
            query_vector = self._provider.embed_text(query)

            # 2. Search the vector store
            chunks = self._vector_store.search_chunks(query_vector=query_vector, limit=limit)
            
            logger.info("Retrieved %d chunks for query '%s'", len(chunks), query)
            
            return AgentResult.success(
                value=chunks,
                metadata={
                    "retrieved_count": len(chunks),
                    "query_length": len(query)
                }
            )

        except ProviderError as exc:
            logger.error("Query embedding generation failed: %s", exc)
            return AgentResult.failure(error=exc)
        except Exception as exc:
            logger.exception("Unexpected error during chunk retrieval: %s", exc)
            wrapped_err = RuntimeError(f"Unexpected retrieval error: {exc}")
            return AgentResult.failure(error=wrapped_err)

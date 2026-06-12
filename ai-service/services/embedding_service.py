"""
EmbeddingService — orchestrates generating vectors and storing knowledge.
"""

from __future__ import annotations

import logging

from core.result import AgentResult
from core.exceptions import ProviderError
from embeddings.base import EmbeddingProvider
from vectorstores.base import VectorStore
from models.knowledge_document import KnowledgeDocument
from models.knowledge_chunk import KnowledgeChunk

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service responsible for converting static KnowledgeDocuments into 
    embeddings and persisting them into a VectorStore.
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
        logger.info("EmbeddingService initialized")

    def process_and_store(self, document: KnowledgeDocument) -> AgentResult[bool]:
        """
        Embed a single document and store it.

        Args:
            document: The validated KnowledgeDocument to store.

        Returns:
            AgentResult.success(True) on success, or a failure result on error.
        """
        logger.info("Processing document '%s' (category: %s)", document.title, document.category)

        try:
            # 1. Generate the embedding vector
            # For this phase, we embed the entire content.
            # In a real implementation, chunking logic might go here.
            vector = self._provider.embed_text(document.content)

            # 2. Store the document + vector
            self._vector_store.upsert_documents([document], [vector])

            logger.info("Successfully stored document '%s'", document.title)
            return AgentResult.success(
                value=True,
                metadata={
                    "document_id": document.id,
                    "vector_dimension": len(vector)
                }
            )

        except ProviderError as exc:
            logger.error("Embedding generation failed for document '%s': %s", document.title, exc)
            return AgentResult.failure(error=exc, metadata={"document_id": document.id})
        except Exception as exc:
            logger.exception("Unexpected error processing document '%s': %s", document.title, exc)
            wrapped_err = RuntimeError(f"Unexpected service error: {exc}")
            return AgentResult.failure(error=wrapped_err, metadata={"document_id": document.id})

    def process_batch(self, documents: list[KnowledgeDocument]) -> AgentResult[int]:
        """
        Embed a batch of documents and store them efficiently.

        Args:
            documents: A list of KnowledgeDocuments.

        Returns:
            AgentResult.success(int) with the number of processed documents.
        """
        if not documents:
            return AgentResult.success(0)

        logger.info("Processing batch of %d documents", len(documents))

        try:
            texts = [doc.content for doc in documents]
            vectors = self._provider.embed_batch(texts)
            
            self._vector_store.upsert_documents(documents, vectors)
            
            logger.info("Successfully stored batch of %d documents", len(documents))
            return AgentResult.success(
                value=len(documents),
                metadata={
                    "batch_size": len(documents),
                    "vector_dimension": len(vectors[0]) if vectors else 0
                }
            )
            
        except ProviderError as exc:
            logger.error("Batch embedding generation failed: %s", exc)
            return AgentResult.failure(error=exc)
        except Exception as exc:
            logger.exception("Unexpected error processing batch: %s", exc)
            wrapped_err = RuntimeError(f"Unexpected service error: {exc}")
            return AgentResult.failure(error=wrapped_err)

    def process_and_store_chunks(self, chunks: list[KnowledgeChunk]) -> AgentResult[int]:
        """
        Embed a batch of chunks and store them efficiently.

        Args:
            chunks: A list of KnowledgeChunks.

        Returns:
            AgentResult.success(int) with the number of processed chunks.
        """
        if not chunks:
            return AgentResult.success(0)

        logger.info("Processing batch of %d chunks", len(chunks))

        try:
            texts = [chunk.content for chunk in chunks]
            vectors = self._provider.embed_batch(texts)
            
            self._vector_store.upsert_chunks(chunks, vectors)
            
            logger.info("Successfully stored batch of %d chunks", len(chunks))
            return AgentResult.success(
                value=len(chunks),
                metadata={
                    "batch_size": len(chunks),
                    "vector_dimension": len(vectors[0]) if vectors else 0
                }
            )
            
        except ProviderError as exc:
            logger.error("Batch embedding generation failed for chunks: %s", exc)
            return AgentResult.failure(error=exc)
        except Exception as exc:
            logger.exception("Unexpected error processing chunks: %s", exc)
            wrapped_err = RuntimeError(f"Unexpected service error: {exc}")
            return AgentResult.failure(error=wrapped_err)

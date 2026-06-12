"""
VectorStore abstract base class.
"""

from __future__ import annotations

import abc

from models.knowledge_document import KnowledgeDocument
from models.knowledge_chunk import KnowledgeChunk


class VectorStore(abc.ABC):
    """
    Abstract Base Class for a Vector Database.

    This isolates the application layer from the specific database implementation
    (e.g., Qdrant, Pinecone, Weaviate).
    """

    @abc.abstractmethod
    def upsert_documents(self, documents: list[KnowledgeDocument], embeddings: list[list[float]]) -> None:
        """
        Insert or update documents and their corresponding embeddings in the store.

        Args:
            documents: List of KnowledgeDocument domain objects.
            embeddings: List of embedding vectors corresponding to the documents.
        """
        pass

    @abc.abstractmethod
    def search(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeDocument]:
        """
        Search the vector store for documents similar to the query vector.

        Args:
            query_vector: The embedded representation of the search query.
            limit: Maximum number of results to return.

        Returns:
            List of KnowledgeDocument objects ordered by relevance.
        """
        pass

    @abc.abstractmethod
    def upsert_chunks(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> None:
        """
        Insert or update chunks and their corresponding embeddings in the store.

        Args:
            chunks: List of KnowledgeChunk domain objects.
            embeddings: List of embedding vectors corresponding to the chunks.
        """
        pass

    @abc.abstractmethod
    def search_chunks(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeChunk]:
        """
        Search the vector store for chunks similar to the query vector.

        Args:
            query_vector: The embedded representation of the search query.
            limit: Maximum number of results to return.

        Returns:
            List of KnowledgeChunk objects ordered by relevance.
        """
        pass

    @abc.abstractmethod
    def delete(self, document_id: str) -> bool:
        """
        Delete a document from the vector store by its ID.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if the document was found and deleted, False otherwise.
        """
        pass

    @abc.abstractmethod
    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        """
        Retrieve a single document by its ID.

        Args:
            document_id: The ID of the document to retrieve.

        Returns:
            The KnowledgeDocument if found, None otherwise.
        """
        pass

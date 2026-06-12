"""
Qdrant implementation of the VectorStore.
"""

from __future__ import annotations

import logging
import time

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_http_exceptions
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from config.settings import settings
from core.exceptions import QdrantConnectionError, QdrantSearchError
from models.knowledge_document import KnowledgeDocument
from models.knowledge_chunk import KnowledgeChunk
from vectorstores.base import VectorStore

logger = logging.getLogger(__name__)

class QdrantVectorStore(VectorStore):
    """
    Production Qdrant Vector Store utilizing the official qdrant-client.
    Includes idempotent collection creation and structured logging.
    """

    def __init__(self) -> None:
        """
        Initialize the Qdrant connection and ensure the collection exists.
        Reads config from settings.
        """
        self.host = settings.qdrant_host
        self.port = settings.qdrant_port
        self.collection_name = settings.qdrant_collection
        
        # We assume 768 for gemini text-embedding models unless overriden.
        self.dimension = 768

        try:
            # If a full URL and API key are provided, use those (Qdrant Cloud)
            if settings.qdrant_url and settings.qdrant_api_key:
                self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
                logger.info("Initialized QdrantVectorStore via cloud URL, collection='%s'", self.collection_name)
            else:
                # Fallback to local host/port (Docker)
                self.client = QdrantClient(host=self.host, port=self.port)
                logger.info("Initialized QdrantVectorStore on %s:%d, collection='%s'", self.host, self.port, self.collection_name)
                
            self._ensure_collection_exists()
        except Exception as exc:
            raise QdrantConnectionError(f"Failed to initialize QdrantClient: {exc}") from exc

    def _ensure_collection_exists(self) -> None:
        """
        Check if the collection exists, and create it if it does not.
        Idempotent operation.
        """
        try:
            collections_response = self.client.get_collections()
            exists = any(col.name == self.collection_name for col in collections_response.collections)
            
            if not exists:
                logger.info("Collection '%s' does not exist. Creating it with dimension=%d", self.collection_name, self.dimension)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                )
        except Exception as exc:
            logger.error("Failed to ensure collection exists: %s", exc)
            raise QdrantConnectionError(f"Failed to check/create collection: {exc}") from exc

    def upsert_documents(self, documents: list[KnowledgeDocument], embeddings: list[list[float]]) -> None:
        """
        Insert or update documents and their corresponding embeddings in the store.
        """
        if len(documents) != len(embeddings):
            raise ValueError("Mismatched documents and embeddings length.")
            
        if not documents:
            return

        points = []
        for doc, emb in zip(documents, embeddings):
            points.append(
                PointStruct(
                    id=doc.id,
                    vector=emb,
                    payload=doc.model_dump(mode="json")
                )
            )

        start_time = time.perf_counter()
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info("Upserted %d documents into Qdrant in %.2fms", len(points), duration)
        except qdrant_http_exceptions.UnexpectedResponse as exc:
            logger.error("Qdrant upsert failed: %s", exc)
            raise QdrantConnectionError(f"Failed to upsert points: {exc}") from exc

    def search(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeDocument]:
        """
        Search the vector store for documents similar to the query vector.
        """
        start_time = time.perf_counter()
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info("Qdrant search completed in %.2fms, found %d results", duration, len(results))
            
            docs = []
            for hit in results:
                if hit.payload:
                    docs.append(KnowledgeDocument.model_validate(hit.payload))
            return docs
            
        except qdrant_http_exceptions.UnexpectedResponse as exc:
            logger.error("Qdrant search failed: %s", exc)
            raise QdrantSearchError(f"Search failed: {exc}") from exc

    def upsert_chunks(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> None:
        """
        Insert or update chunks and their corresponding embeddings in the store.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Mismatched chunks and embeddings length.")
            
        if not chunks:
            return

        points = []
        for chunk, emb in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=chunk.id,
                    vector=emb,
                    payload={"_is_chunk": True, **chunk.model_dump(mode="json")}
                )
            )

        start_time = time.perf_counter()
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info("Upserted %d chunks into Qdrant in %.2fms", len(points), duration)
        except qdrant_http_exceptions.UnexpectedResponse as exc:
            logger.error("Qdrant upsert chunks failed: %s", exc)
            raise QdrantConnectionError(f"Failed to upsert points: {exc}") from exc

    def search_chunks(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeChunk]:
        """
        Search the vector store for chunks similar to the query vector.
        """
        start_time = time.perf_counter()
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True
            )
            duration = (time.perf_counter() - start_time) * 1000
            logger.info("Qdrant search chunks completed in %.2fms, found %d results", duration, len(results))
            
            chunks = []
            for hit in results:
                if hit.payload and hit.payload.get("_is_chunk"):
                    # Remove the internal flag before validation
                    payload_data = dict(hit.payload)
                    payload_data.pop("_is_chunk", None)
                    chunks.append(KnowledgeChunk.model_validate(payload_data))
            return chunks
            
        except qdrant_http_exceptions.UnexpectedResponse as exc:
            logger.error("Qdrant search chunks failed: %s", exc)
            raise QdrantSearchError(f"Search failed: {exc}") from exc

    def delete(self, document_id: str) -> bool:
        """
        Delete a document from the vector store by its ID.
        """
        try:
            response = self.client.delete(
                collection_name=self.collection_name,
                points_selector=[document_id],
            )
            return response.status == "completed"
        except Exception as exc:
            logger.error("Qdrant delete failed for id=%s: %s", document_id, exc)
            raise QdrantConnectionError(f"Delete failed: {exc}") from exc

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        """
        Retrieve a single document by its ID.
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[document_id],
                with_payload=True
            )
            if not points:
                return None
                
            payload = points[0].payload
            if not payload:
                return None
                
            return KnowledgeDocument.model_validate(payload)
        except Exception as exc:
            logger.error("Qdrant retrieve failed for id=%s: %s", document_id, exc)
            raise QdrantConnectionError(f"Retrieve failed: {exc}") from exc

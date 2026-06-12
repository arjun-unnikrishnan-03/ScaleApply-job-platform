"""
KnowledgeIndexer — orchestrates loading documents and passing them to the EmbeddingService.
"""

from __future__ import annotations

import logging
import time

from core.result import AgentResult
from models.indexing_report import IndexingReport
from loaders.knowledge_loader import KnowledgeLoader
from services.embedding_service import EmbeddingService
from services.chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """
    Coordinates the indexing of local knowledge files into the VectorStore.
    
    It binds together the KnowledgeLoader and the EmbeddingService without
    knowing the specifics of either.
    """

    def __init__(self, loader: KnowledgeLoader, embedding_service: EmbeddingService, chunking_service: ChunkingService | None = None) -> None:
        """
        Initialize the indexer.

        Args:
            loader: Component responsible for providing KnowledgeDocuments.
            embedding_service: Component responsible for embedding and storing.
            chunking_service: Optional service for chunking documents before indexing.
        """
        self._loader = loader
        self._embedding_service = embedding_service
        self._chunking_service = chunking_service

    def index_all(self) -> AgentResult[IndexingReport]:
        """
        Run the full indexing pipeline.
        
        Returns:
            An AgentResult containing the IndexingReport.
        """
        start_time = time.perf_counter()
        logger.info("Starting knowledge indexing pipeline.")

        try:
            # 1. Load documents from disk
            documents = self._loader.load_documents()
            
            if not documents:
                logger.warning("No documents found to index.")
                report = IndexingReport(
                    total_documents=0,
                    indexed_documents=0,
                    failed_documents=0,
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
                return AgentResult.success(report)

            # 2. Process documents
            total = len(documents)
            success_count = 0
            failed_count = 0

            if self._chunking_service:
                logger.info("Using chunk-aware indexing.")
                all_chunks = []
                for doc in documents:
                    all_chunks.extend(self._chunking_service.chunk_document(doc))
                
                batch_result = self._embedding_service.process_and_store_chunks(all_chunks)
                if batch_result.is_success:
                    success_count = total
                else:
                    failed_count = total
                    logger.error("Batch chunk indexing failed: %s", batch_result.error)
            else:
                batch_result = self._embedding_service.process_batch(documents)
                
                if batch_result.is_success:
                    success_count = batch_result.unwrap()
                else:
                    # If batch fails completely, all are failed
                    failed_count = total
                    logger.error("Batch indexing failed: %s", batch_result.error)

            duration_ms = (time.perf_counter() - start_time) * 1000

            report = IndexingReport(
                total_documents=total,
                indexed_documents=success_count,
                failed_documents=failed_count,
                duration_ms=duration_ms
            )
            
            logger.info(
                "Indexing complete. Total: %d | Success: %d | Failed: %d | Time: %.2fms",
                total, success_count, failed_count, duration_ms
            )
            return AgentResult.success(report)

        except Exception as exc:
            logger.exception("Unexpected error during indexing: %s", exc)
            wrapped_err = RuntimeError(f"Indexing pipeline failed: {exc}")
            return AgentResult.failure(error=wrapped_err)

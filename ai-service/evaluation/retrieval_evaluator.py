"""
RetrievalEvaluator — a framework for testing and measuring vector retrieval quality.
"""

from __future__ import annotations

import logging
import time

from models.retrieval_metrics import RetrievalMetrics
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class RetrievalEvaluator:
    """
    Evaluates the quality of a RetrievalService by simulating queries
    and checking if the expected documents are retrieved in the top K results.
    """

    def __init__(self, retrieval_service: RetrievalService) -> None:
        """
        Args:
            retrieval_service: The service to evaluate.
        """
        self._retrieval_service = retrieval_service

    def evaluate(self, question: str, expected_document_id: str, expected_category: str | None = None) -> RetrievalMetrics:
        """
        Run a single query and calculate the retrieval metrics.

        Args:
            question: The natural language search query.
            expected_document_id: The document ID that MUST be retrieved.
            expected_category: (Optional) The category the document should belong to.

        Returns:
            A RetrievalMetrics domain model.
        """
        logger.info("Evaluating retrieval for question: '%s' (expected doc: %s)", question, expected_document_id)

        start_time = time.perf_counter()
        
        # We request up to 5 results to evaluate top_1, top_3, and top_5
        result = self._retrieval_service.retrieve_chunks(query=question, limit=5)
        
        duration_ms = (time.perf_counter() - start_time) * 1000

        if not result.is_success:
            logger.error("Retrieval failed during evaluation: %s", result.error)
            return RetrievalMetrics(
                top_1_hit=False,
                top_3_hit=False,
                top_5_hit=False,
                latency_ms=duration_ms,
                retrieved_documents=0
            )

        chunks = result.unwrap()
        retrieved_count = len(chunks)
        
        top_1_hit = False
        top_3_hit = False
        top_5_hit = False

        for i, chunk in enumerate(chunks):
            # Check if this chunk belongs to the expected document
            is_match = chunk.document_id == expected_document_id
            
            if is_match and expected_category:
                is_match = chunk.category == expected_category

            if is_match:
                if i < 1:
                    top_1_hit = True
                if i < 3:
                    top_3_hit = True
                if i < 5:
                    top_5_hit = True
                break

        metrics = RetrievalMetrics(
            top_1_hit=top_1_hit,
            top_3_hit=top_3_hit,
            top_5_hit=top_5_hit,
            latency_ms=duration_ms,
            retrieved_documents=retrieved_count
        )
        
        logger.info(
            "Evaluation complete: top1=%s, top3=%s, top5=%s, latency=%.2fms",
            top_1_hit, top_3_hit, top_5_hit, duration_ms
        )

        return metrics

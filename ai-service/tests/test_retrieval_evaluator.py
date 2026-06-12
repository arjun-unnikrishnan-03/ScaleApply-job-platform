"""
Tests for RetrievalEvaluator.
"""

from unittest.mock import MagicMock

from core.result import AgentResult
from evaluation.retrieval_evaluator import RetrievalEvaluator
from models.knowledge_chunk import KnowledgeChunk

def test_retrieval_evaluator_top_1_hit():
    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = AgentResult.success([
        KnowledgeChunk(document_id="doc-1", title="T1", category="C1", chunk_index=0, content="Content 1"),
        KnowledgeChunk(document_id="doc-2", title="T2", category="C2", chunk_index=0, content="Content 2"),
    ])
    
    evaluator = RetrievalEvaluator(retrieval_service=mock_service)
    metrics = evaluator.evaluate(question="Query", expected_document_id="doc-1")
    
    assert metrics.top_1_hit is True
    assert metrics.top_3_hit is True
    assert metrics.top_5_hit is True
    assert metrics.retrieved_documents == 2

def test_retrieval_evaluator_top_3_hit():
    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = AgentResult.success([
        KnowledgeChunk(document_id="doc-2", title="T2", category="C2", chunk_index=0, content="C"),
        KnowledgeChunk(document_id="doc-3", title="T3", category="C3", chunk_index=0, content="C"),
        KnowledgeChunk(document_id="doc-1", title="T1", category="C1", chunk_index=0, content="C"),
    ])
    
    evaluator = RetrievalEvaluator(retrieval_service=mock_service)
    metrics = evaluator.evaluate(question="Query", expected_document_id="doc-1")
    
    assert metrics.top_1_hit is False
    assert metrics.top_3_hit is True
    assert metrics.top_5_hit is True

def test_retrieval_evaluator_miss():
    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = AgentResult.success([
        KnowledgeChunk(document_id="doc-2", title="T2", category="C2", chunk_index=0, content="C"),
    ])
    
    evaluator = RetrievalEvaluator(retrieval_service=mock_service)
    metrics = evaluator.evaluate(question="Query", expected_document_id="doc-1")
    
    assert metrics.top_1_hit is False
    assert metrics.top_3_hit is False
    assert metrics.top_5_hit is False

def test_retrieval_evaluator_category_mismatch():
    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = AgentResult.success([
        KnowledgeChunk(document_id="doc-1", title="T1", category="WRONG", chunk_index=0, content="C"),
    ])
    
    evaluator = RetrievalEvaluator(retrieval_service=mock_service)
    metrics = evaluator.evaluate(question="Query", expected_document_id="doc-1", expected_category="RIGHT")
    
    assert metrics.top_1_hit is False

def test_retrieval_evaluator_service_failure():
    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = AgentResult.failure(error=RuntimeError("Fail"))
    
    evaluator = RetrievalEvaluator(retrieval_service=mock_service)
    metrics = evaluator.evaluate(question="Query", expected_document_id="doc-1")
    
    assert metrics.top_1_hit is False
    assert metrics.retrieved_documents == 0
    assert metrics.latency_ms >= 0

"""
Tests for RetrievalResult and KnowledgeResponse domain models.
"""

import pytest
from pydantic import ValidationError

from models.retrieval_result import RetrievalResult
from models.knowledge_response import KnowledgeResponse
from models.knowledge_document import KnowledgeDocument

def test_retrieval_result_valid():
    doc = KnowledgeDocument(title="T", category="C", content="C")
    res = RetrievalResult(query="test", documents=[doc], scores=[1.0])
    assert res.query == "test"
    assert len(res.documents) == 1
    assert res.scores[0] == 1.0

def test_knowledge_response_valid():
    res = KnowledgeResponse(
        answer="The answer is 42.",
        sources=["doc1.md"],
        confidence=0.9
    )
    assert res.answer == "The answer is 42."
    assert len(res.sources) == 1
    assert res.confidence == 0.9

def test_knowledge_response_invalid_confidence():
    with pytest.raises(ValidationError):
        KnowledgeResponse(answer="A", sources=["s"], confidence=1.5)
        
    with pytest.raises(ValidationError):
        KnowledgeResponse(answer="A", sources=["s"], confidence=-0.5)

def test_knowledge_response_deduplicate_sources():
    res = KnowledgeResponse(
        answer="A",
        sources=["doc1", "Doc1", "  doc1  ", "doc2"],
        confidence=0.5
    )
    assert len(res.sources) == 2
    assert "doc1" in res.sources
    assert "doc2" in res.sources

def test_knowledge_response_missing_answer():
    with pytest.raises(ValidationError):
        KnowledgeResponse(answer="", sources=["s"], confidence=0.5)

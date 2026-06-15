"""
Tests for KnowledgeDocument and EmbeddingResult.
"""

import pytest
from pydantic import ValidationError

from models.knowledge_document import KnowledgeDocument
from models.embedding_result import EmbeddingResult

def test_knowledge_document_valid_construction():
    doc = KnowledgeDocument(
        title="Docker Basics",
        category="Skills",
        content="Docker is a containerization platform.",
        tags=["docker", "containers"]
    )
    assert doc.id is not None
    assert doc.title == "Docker Basics"
    assert doc.category == "Skills"
    assert doc.content == "Docker is a containerization platform."
    assert len(doc.tags) == 2

def test_knowledge_document_missing_required_fields():
    with pytest.raises(ValidationError):
        KnowledgeDocument(title="Missing Category and Content")

def test_knowledge_document_tag_deduplication():
    doc = KnowledgeDocument(
        title="Tags Test",
        category="Test",
        content="Testing tags",
        tags=["AWS", "aws", "  AWS  ", "Cloud"]
    )
    assert len(doc.tags) == 2
    assert "AWS" in doc.tags
    assert "Cloud" in doc.tags

def test_knowledge_document_is_frozen():
    doc = KnowledgeDocument(title="T", category="C", content="C")
    with pytest.raises(Exception):
        doc.title = "New Title"  # type: ignore

def test_embedding_result_valid_construction():
    res = EmbeddingResult(document_id="123", vector=[0.1, 0.2, 0.3])
    assert res.document_id == "123"
    assert len(res.vector) == 3

def test_embedding_result_empty_vector_raises():
    with pytest.raises(ValidationError):
        EmbeddingResult(document_id="123", vector=[])

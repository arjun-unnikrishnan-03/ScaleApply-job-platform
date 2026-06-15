"""
Tests for KnowledgeChunk domain model.
"""

import pytest
from pydantic import ValidationError

from models.knowledge_chunk import KnowledgeChunk

def test_knowledge_chunk_valid_creation():
    chunk = KnowledgeChunk(
        document_id="doc-123",
        title="Test Title",
        category="Test Category",
        chunk_index=0,
        content="This is the content.",
        tags=["python", "ai"]
    )
    
    assert chunk.document_id == "doc-123"
    assert chunk.title == "Test Title"
    assert chunk.category == "Test Category"
    assert chunk.chunk_index == 0
    assert chunk.content == "This is the content."
    assert chunk.tags == ["python", "ai"]

def test_knowledge_chunk_id_generated():
    chunk1 = KnowledgeChunk(
        document_id="doc-1", title="T", category="C", chunk_index=1, content="C"
    )
    chunk2 = KnowledgeChunk(
        document_id="doc-1", title="T", category="C", chunk_index=2, content="C"
    )
    assert chunk1.id != chunk2.id

def test_knowledge_chunk_invalid_chunk_index():
    with pytest.raises(ValidationError):
        KnowledgeChunk(
            document_id="doc-1", title="T", category="C", chunk_index=-1, content="C"
        )

def test_knowledge_chunk_deduplicates_tags():
    chunk = KnowledgeChunk(
        document_id="doc-1",
        title="T",
        category="C",
        chunk_index=0,
        content="C",
        tags=["Python", "python", " AI ", "ai"]
    )
    assert set(chunk.tags) == {"Python", "AI"}
    assert len(chunk.tags) == 2

def test_knowledge_chunk_forbids_extra_fields():
    with pytest.raises(ValidationError):
        KnowledgeChunk(
            document_id="doc-1",
            title="T",
            category="C",
            chunk_index=0,
            content="C",
            extra_field="not allowed"
        )

def test_knowledge_chunk_is_frozen():
    chunk = KnowledgeChunk(
        document_id="doc-1", title="T", category="C", chunk_index=0, content="C"
    )
    with pytest.raises(ValidationError):
        chunk.title = "New Title"

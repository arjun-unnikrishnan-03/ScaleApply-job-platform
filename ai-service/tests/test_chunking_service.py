"""
Tests for ChunkingService.
"""

from unittest.mock import MagicMock

from models.knowledge_chunk import KnowledgeChunk
from models.knowledge_document import KnowledgeDocument
from services.chunking_service import ChunkingService

def test_chunking_service_delegates_to_chunker():
    mock_chunker = MagicMock()
    mock_chunker.chunk.return_value = [
        KnowledgeChunk(document_id="1", title="T", category="C", chunk_index=0, content="C1"),
        KnowledgeChunk(document_id="1", title="T", category="C", chunk_index=1, content="C2")
    ]
    
    service = ChunkingService(chunker=mock_chunker)
    doc = KnowledgeDocument(title="T", category="C", content="C1\nC2")
    
    chunks = service.chunk_document(doc)
    
    mock_chunker.chunk.assert_called_once_with(doc)
    assert len(chunks) == 2
    assert chunks[0].content == "C1"
    assert chunks[1].content == "C2"

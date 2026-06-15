"""
Tests for MarkdownChunker.
"""

from chunkers.markdown_chunker import MarkdownChunker
from models.knowledge_document import KnowledgeDocument

from unittest.mock import MagicMock

def test_markdown_chunker_empty_document():
    doc = MagicMock()
    doc.content = "   "
    chunker = MarkdownChunker()
    chunks = chunker.chunk(doc)
    assert len(chunks) == 0

def test_markdown_chunker_no_headers():
    doc = KnowledgeDocument(title="T", category="C", content="Just some text.\n\nMore text.")
    chunker = MarkdownChunker()
    chunks = chunker.chunk(doc)
    assert len(chunks) == 1
    assert chunks[0].content == "Just some text.\n\nMore text."
    assert chunks[0].chunk_index == 0
    assert chunks[0].title == "T"

def test_markdown_chunker_with_headers():
    content = """# Header 1
Content 1

## Header 2
Content 2
"""
    doc = KnowledgeDocument(title="T", category="C", content=content)
    chunker = MarkdownChunker()
    chunks = chunker.chunk(doc)
    
    assert len(chunks) == 2
    assert chunks[0].content == "# Header 1\n\nContent 1"
    assert chunks[0].chunk_index == 0
    assert chunks[1].content == "## Header 2\n\nContent 2"
    assert chunks[1].chunk_index == 1

def test_markdown_chunker_long_section_sliding_window():
    # Create a long section with paragraphs
    content = "# Long Header\n\n"
    content += "A" * 100 + "\n\n"
    content += "B" * 100 + "\n\n"
    content += "C" * 100 + "\n\n"
    
    doc = KnowledgeDocument(title="T", category="C", content=content)
    
    # Configure chunker with max length 150, overlap 20
    chunker = MarkdownChunker(max_chunk_length=150, overlap=20)
    chunks = chunker.chunk(doc)
    
    # Should split into multiple chunks because each paragraph + header exceeds 150 eventually
    assert len(chunks) > 1
    
    # Verify index sequence
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert len(chunk.content) <= 200 # approximate with overlaps

"""
Markdown chunker implementation for splitting text by markdown headers.
"""

from __future__ import annotations

import re

from chunkers.base import Chunker
from models.knowledge_chunk import KnowledgeChunk
from models.knowledge_document import KnowledgeDocument


class MarkdownChunker(Chunker):
    """
    Chunks a KnowledgeDocument based on markdown headers.
    Falls back to a sliding window of paragraphs/lines if a section is too long.
    """

    def __init__(self, max_chunk_length: int = 2000, overlap: int = 200):
        """
        Args:
            max_chunk_length: Target max characters per chunk (approximate token window).
            overlap: Target character overlap between sliding window chunks if a section is split.
        """
        self.max_chunk_length = max_chunk_length
        self.overlap = overlap

    def chunk(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        if not document.content or not document.content.strip():
            return []

        # Split by markdown headers (e.g., # Header, ## Header)
        # Using a regex that captures the header and the content that follows it.
        # This regex looks for start of line, 1-6 hashes, a space, and the header text.
        header_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
        
        # re.split will return [content_before_first_header, header1, content1, header2, content2...]
        parts = header_pattern.split(document.content)
        
        sections = []
        
        # If there's content before the first header, it's at index 0.
        if parts[0].strip():
            sections.append(parts[0].strip())
            
        # Iterate over header-content pairs
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            content = parts[i+1].strip() if i+1 < len(parts) else ""
            
            combined = f"{header}\n\n{content}".strip()
            if combined:
                sections.append(combined)

        chunks = []
        chunk_index = 0
        
        for section in sections:
            # If the section itself is small enough, it becomes one chunk
            if len(section) <= self.max_chunk_length:
                if section.strip():
                    chunks.append(
                        KnowledgeChunk(
                            document_id=document.id,
                            title=document.title,
                            category=document.category,
                            chunk_index=chunk_index,
                            content=section,
                            tags=document.tags,
                        )
                    )
                    chunk_index += 1
            else:
                # If section is too long, we apply a sliding window fallback
                # To maintain some semantic boundary, we split by paragraphs first
                paragraphs = section.split("\n\n")
                
                current_chunk_text = ""
                
                for p in paragraphs:
                    if len(current_chunk_text) + len(p) + 2 > self.max_chunk_length and current_chunk_text:
                        # Yield the current chunk
                        chunks.append(
                            KnowledgeChunk(
                                document_id=document.id,
                                title=document.title,
                                category=document.category,
                                chunk_index=chunk_index,
                                content=current_chunk_text.strip(),
                                tags=document.tags,
                            )
                        )
                        chunk_index += 1
                        
                        # Start new chunk with overlap
                        # Find the end of the previous chunk to use as overlap
                        if len(current_chunk_text) > self.overlap:
                            # Try to find a clean break (e.g., last newline) in the overlap region
                            overlap_start = len(current_chunk_text) - self.overlap
                            newline_pos = current_chunk_text.find("\n", overlap_start)
                            
                            if newline_pos != -1:
                                current_chunk_text = current_chunk_text[newline_pos:].strip() + "\n\n" + p
                            else:
                                current_chunk_text = current_chunk_text[overlap_start:].strip() + "\n\n" + p
                        else:
                            current_chunk_text = p
                    else:
                        if current_chunk_text:
                            current_chunk_text += "\n\n" + p
                        else:
                            current_chunk_text = p
                
                # Yield the last piece of this section
                if current_chunk_text.strip():
                    chunks.append(
                        KnowledgeChunk(
                            document_id=document.id,
                            title=document.title,
                            category=document.category,
                            chunk_index=chunk_index,
                            content=current_chunk_text.strip(),
                            tags=document.tags,
                        )
                    )
                    chunk_index += 1

        return chunks

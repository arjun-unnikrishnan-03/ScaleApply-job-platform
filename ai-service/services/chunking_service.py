"""
ChunkingService - orchestrates transforming a KnowledgeDocument into KnowledgeChunks.
"""

from __future__ import annotations

import logging

from chunkers.base import Chunker
from models.knowledge_chunk import KnowledgeChunk
from models.knowledge_document import KnowledgeDocument

logger = logging.getLogger(__name__)

class ChunkingService:
    """
    Service responsible for transforming large knowledge documents into
    smaller semantic chunks using a provided Chunker strategy.
    """

    def __init__(self, chunker: Chunker) -> None:
        """
        Args:
            chunker: The strategy to use for splitting documents.
        """
        self._chunker = chunker

    def chunk_document(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """
        Chunks a KnowledgeDocument into smaller pieces.

        Args:
            document: The document to chunk.

        Returns:
            A list of KnowledgeChunk domain models.
        """
        logger.info("Chunking document '%s' (id=%s)", document.title, document.id)
        
        chunks = self._chunker.chunk(document)
        
        logger.info("Document '%s' yielded %d chunks", document.title, len(chunks))
        return chunks

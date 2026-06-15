"""
Abstract base class for chunking knowledge documents.
"""

from __future__ import annotations

import abc

from models.knowledge_chunk import KnowledgeChunk
from models.knowledge_document import KnowledgeDocument


class Chunker(abc.ABC):
    """
    Abstract Base Class for semantic chunking algorithms.
    """

    @abc.abstractmethod
    def chunk(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """
        Convert a single KnowledgeDocument into a list of KnowledgeChunks.

        Args:
            document: The full source document.

        Returns:
            A list of validated KnowledgeChunk objects.
        """
        pass

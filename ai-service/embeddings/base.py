"""
EmbeddingProvider abstract base class.
"""

from __future__ import annotations

import abc

class EmbeddingProvider(abc.ABC):
    """
    Abstract Base Class for an Embedding Provider.
    
    This isolates the rest of the system from the specifics of Gemini, OpenAI,
    Voyage, or any other embedding model SDKs.
    """

    @abc.abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string into a vector.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        pass

    @abc.abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of text strings into vectors.

        Args:
            texts: The list of text strings to embed.

        Returns:
            A list of embedding vectors (list of list of floats).
        """
        pass

    @abc.abstractmethod
    def get_dimension(self) -> int:
        """
        Return the dimensionality of the generated vectors.
        """
        pass

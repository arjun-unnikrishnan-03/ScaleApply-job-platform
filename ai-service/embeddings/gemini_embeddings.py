"""
Gemini implementation of the EmbeddingProvider.
"""

from __future__ import annotations

import logging
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from core.exceptions import EmbeddingProviderError, GeminiAuthenticationError
from embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Production-ready Gemini Embedding Provider utilizing the official google-generativeai SDK.
    Includes exponential backoff retries for batching and structured logging.
    """

    def __init__(self, api_key: str | None = None, model_name: str | None = None, **kwargs) -> None:
        """
        Initialize the Gemini embedding provider.
        Reads config from settings.
        """
        self.api_key = api_key or settings.gemini_api_key or settings.llm_api_key
        self.model_name = model_name or settings.embedding_model
        
        # We assume 768 for gemini text-embedding models unless overriden.
        # Ideally we'd fetch this dynamically or put in settings, but it's a known constant.
        self.dimension = 768  

        if not self.api_key:
            raise GeminiAuthenticationError("Gemini API key is not configured for embeddings.")

        genai.configure(api_key=self.api_key)
        logger.info("Initialized GeminiEmbeddingProvider targeted at model '%s'", self.model_name)

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string into a vector.
        """
        if not text or not text.strip():
            raise EmbeddingProviderError("Cannot embed an empty string.")

        try:
            res = self._execute_embed_with_retry([text])
            return res[0]
        except google_exceptions.GoogleAPIError as exc:
            raise EmbeddingProviderError(f"SDK Error: {exc}") from exc

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of text strings into vectors.
        """
        if not texts:
            return []

        all_embeddings = []
        batch_size = settings.embedding_batch_size
        
        start_time = time.perf_counter()
        
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            try:
                embeddings = self._execute_embed_with_retry(chunk)
                all_embeddings.extend(embeddings)
            except Exception as exc:
                logger.error("Failed to embed chunk %d-%d: %s", i, i + len(chunk), exc)
                raise EmbeddingProviderError(f"Batch embedding failed at chunk {i}: {exc}") from exc

        duration = (time.perf_counter() - start_time) * 1000
        logger.info("Embedded %d texts in %.2fms", len(texts), duration)
        
        return all_embeddings

    def get_dimension(self) -> int:
        """Return the dimensionality of the generated vectors."""
        return self.dimension

    @retry(
        retry=retry_if_exception_type((
            google_exceptions.ResourceExhausted,
            google_exceptions.InternalServerError,
            google_exceptions.ServiceUnavailable,
            google_exceptions.GatewayTimeout,
        )),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(settings.gemini_max_retries),
        reraise=True
    )
    def _execute_embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Execute the SDK embed call with tenacity retry policies."""
        logger.debug("Sending embed request to Gemini for %d texts", len(texts))
        
        # For Gemini, the embed_content endpoint accepts a single string or a list of strings
        result = genai.embed_content(
            model=self.model_name,
            content=texts,
            task_type="retrieval_document", # Suitable for generic knowledge base indexing
            output_dimensionality=self.dimension
        )
        
        # genai returns a dict like {'embedding': [ [float, ...], ... ]}
        # if passed a list, or just a flat list if passed a single string.
        # but usually it returns a list of dictionaries if passed a list, or 
        # a dictionary with a list of lists.
        # Official structure: result['embedding'] contains the list(s).
        embeddings = result.get("embedding")
        if not embeddings:
            raise EmbeddingProviderError("Gemini API returned empty embeddings.")
            
        # If we passed a single text, the SDK might return a flat list instead of nested.
        # We enforce nested lists to handle uniformly since we always pass a list to the SDK here.
        if len(texts) == 1 and not isinstance(embeddings[0], list):
            return [embeddings]
            
        return embeddings

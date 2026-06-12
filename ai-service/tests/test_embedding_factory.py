"""
Tests for EmbeddingFactory and GeminiEmbeddingProvider.
"""

import pytest
from unittest.mock import patch

from core.exceptions import ProviderError
from embeddings.base import EmbeddingProvider
from embeddings.factory import EmbeddingFactory
from embeddings.gemini_embeddings import GeminiEmbeddingProvider

def test_gemini_is_registered():
    assert "gemini" in EmbeddingFactory.available_providers()

def test_create_gemini_provider():
    provider = EmbeddingFactory.create("gemini", api_key="test")
    assert isinstance(provider, GeminiEmbeddingProvider)
    assert provider.api_key == "test"

def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        EmbeddingFactory.create("unknown")

@patch("embeddings.gemini_embeddings.genai")
def test_gemini_provider_embed_text(mock_genai):
    mock_genai.embed_content.return_value = {"embedding": [[0.1] * 768]}
    provider = GeminiEmbeddingProvider(api_key="test-key")
    vector = provider.embed_text("test")
    assert len(vector) == 768
    
@patch("embeddings.gemini_embeddings.genai")
def test_gemini_provider_embed_empty_text_raises(mock_genai):
    provider = GeminiEmbeddingProvider(api_key="test-key")
    with pytest.raises(ProviderError):
        provider.embed_text("   ")

@patch("embeddings.gemini_embeddings.genai")
def test_gemini_provider_embed_batch(mock_genai):
    mock_genai.embed_content.return_value = {"embedding": [[0.1] * 768, [0.2] * 768]}
    provider = GeminiEmbeddingProvider(api_key="test-key")
    vectors = provider.embed_batch(["test1", "test2"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768

def test_custom_provider_registration():
    class CustomProvider(EmbeddingProvider):
        def embed_text(self, text): return [1.0]
        def embed_batch(self, texts): return [[1.0]]
        def get_dimension(self): return 1
        
    EmbeddingFactory.register("custom", CustomProvider)
    assert "custom" in EmbeddingFactory.available_providers()
    provider = EmbeddingFactory.create("custom")
    assert isinstance(provider, CustomProvider)

"""
Tests for GeminiEmbeddingProvider.
"""

from unittest.mock import MagicMock, patch

import pytest
from google.api_core import exceptions as google_exceptions

from core.exceptions import EmbeddingProviderError, GeminiAuthenticationError
from embeddings.gemini_embeddings import GeminiEmbeddingProvider

@pytest.fixture
def mock_genai():
    with patch("embeddings.gemini_embeddings.genai") as mock:
        yield mock

@pytest.fixture
def provider(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("embeddings.gemini_embeddings.wait_exponential.__call__", lambda self, retry_state: 0.01)
    
    return GeminiEmbeddingProvider(api_key="test-key")

def test_initialization_without_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    with pytest.raises(GeminiAuthenticationError):
        GeminiEmbeddingProvider(api_key="")

def test_embed_text_success(provider, mock_genai):
    mock_genai.embed_content.return_value = {"embedding": [[0.1, 0.2, 0.3]]}
    
    result = provider.embed_text("test string")
    
    assert result == [0.1, 0.2, 0.3]
    mock_genai.embed_content.assert_called_once()

def test_embed_text_empty(provider):
    with pytest.raises(EmbeddingProviderError):
        provider.embed_text("   ")

def test_embed_batch_success(provider, mock_genai, monkeypatch):
    monkeypatch.setattr("embeddings.gemini_embeddings.settings.embedding_batch_size", 2)
    
    # We pass 3 items, so it should batch into sizes of 2 and 1
    mock_genai.embed_content.side_effect = [
        {"embedding": [[0.1], [0.2]]},
        {"embedding": [[0.3]]}
    ]
    
    result = provider.embed_batch(["a", "b", "c"])
    
    assert result == [[0.1], [0.2], [0.3]]
    assert mock_genai.embed_content.call_count == 2

def test_embed_batch_empty_list(provider):
    assert provider.embed_batch([]) == []

def test_rate_limit_retry(provider, mock_genai):
    mock_genai.embed_content.side_effect = [
        google_exceptions.ResourceExhausted("Rate limit"),
        {"embedding": [[0.99]]}
    ]
    
    result = provider.embed_text("retry me")
    assert result == [0.99]
    assert mock_genai.embed_content.call_count == 2

def test_sdk_error_mapping(provider, mock_genai):
    mock_genai.embed_content.side_effect = google_exceptions.InvalidArgument("Bad argument")
    
    with pytest.raises(EmbeddingProviderError):
        provider.embed_text("fail")

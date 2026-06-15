"""
Tests for the production GeminiProvider.
"""

from unittest.mock import MagicMock, patch

import pytest
from google.api_core import exceptions as google_exceptions

from core.exceptions import (
    GeminiAuthenticationError,
    GeminiProviderError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    ProviderResponseError,
)
from providers.base import GenerationConfig
from providers.gemini_provider import GeminiProvider

@pytest.fixture
def mock_genai():
    with patch("providers.gemini_provider.genai") as mock:
        # Mock configure and GenerativeModel
        yield mock

@pytest.fixture
def provider(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    # Prevent tenacity from actually sleeping during tests to speed them up
    monkeypatch.setattr("providers.gemini_provider.wait_exponential.__call__", lambda self, retry_state: 0.01)
    
    # Needs to be re-imported or re-instantiated so env is picked up, 
    # but since we pass api_key directly it's fine.
    return GeminiProvider(api_key="test-key", model_name="test-model")

def test_initialization_without_key(monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "llm_api_key", "")
    with pytest.raises(GeminiAuthenticationError):
        GeminiProvider(api_key="")

def test_successful_generation(provider):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "Hello World"
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 5
    
    provider.model.generate_content.return_value = mock_response
    
    config = GenerationConfig(temperature=0.5)
    response = provider.generate("Test prompt", config=config)
    
    assert response.content == "Hello World"
    assert response.model == "test-model"
    assert response.input_tokens == 10
    assert response.output_tokens == 5
    assert response.raw_metadata["latency_ms"] > 0

def test_empty_prompt_raises(provider):
    with pytest.raises(ProviderResponseError):
        provider.generate("   ")

def test_empty_response_raises(provider):
    mock_response = MagicMock()
    mock_response.text = ""
    provider.model.generate_content.return_value = mock_response
    
    with pytest.raises(ProviderResponseError):
        provider.generate("Test prompt")

def test_authentication_error_mapping(provider):
    provider.model.generate_content.side_effect = google_exceptions.PermissionDenied("Invalid key")
    
    with pytest.raises(GeminiAuthenticationError):
        provider.generate("Test prompt")

def test_timeout_error_mapping(provider):
    provider.model.generate_content.side_effect = google_exceptions.GatewayTimeout("Timeout")
    
    # tenacity should retry GatewayTimeout. Let's see if it exhausts and raises.
    # It will raise the original error, then our block catches it.
    with pytest.raises(GeminiTimeoutError):
        provider.generate("Test prompt")
        
    # Since it's a retryable error, it should be called multiple times
    # settings.gemini_max_retries is 3 by default
    assert provider.model.generate_content.call_count == 3

def test_rate_limit_retry_and_mapping(provider):
    provider.model.generate_content.side_effect = google_exceptions.ResourceExhausted("Rate limit")
    
    with pytest.raises(GeminiRateLimitError):
        provider.generate("Test prompt")
        
    # Tenacity retries up to max_retries (3)
    assert provider.model.generate_content.call_count == 3

def test_success_after_retry(provider):
    mock_response = MagicMock()
    mock_response.text = "Success"
    
    # Fails twice, succeeds on third
    provider.model.generate_content.side_effect = [
        google_exceptions.ResourceExhausted("Rate limit"),
        google_exceptions.ResourceExhausted("Rate limit"),
        mock_response
    ]
    
    response = provider.generate("Test prompt")
    
    assert response.content == "Success"
    assert provider.model.generate_content.call_count == 3

def test_unhandled_sdk_error(provider):
    provider.model.generate_content.side_effect = google_exceptions.InvalidArgument("Bad arg")
    
    # InvalidArgument is not in our retry list, so it fails immediately
    with pytest.raises(GeminiProviderError):
        provider.generate("Test prompt")
        
    assert provider.model.generate_content.call_count == 1

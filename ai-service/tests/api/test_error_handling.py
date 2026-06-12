"""
Tests for global error handling middleware.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies.agents import get_resume_agent
from api.dependencies.providers import get_llm_provider
from api.dependencies.vectorstores import get_embedding_provider, get_vector_store
from core.exceptions import (
    ExtractionError,
    GeminiProviderError,
    QdrantConnectionError,
    ProviderRateLimitError,
    ValidationError as DomainValidationError,
)
from core.result import AgentResult


def _client_with_resume_override(mock_agent):
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: MagicMock()
    app.dependency_overrides[get_embedding_provider] = lambda: MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: MagicMock()
    app.dependency_overrides[get_resume_agent] = lambda: mock_agent
    return TestClient(app, raise_server_exceptions=False)


VALID_RESUME_TEXT = "Jane Doe, experienced software engineer with 5 years in Python and FastAPI development."


def test_gemini_error_returns_503():
    mock_agent = MagicMock()
    mock_agent.process_text.return_value = AgentResult.failure(
        error=GeminiProviderError("Gemini down")
    )
    client = _client_with_resume_override(mock_agent)
    response = client.post("/resume/analyze", json={"text": VALID_RESUME_TEXT})
    assert response.status_code == 503
    assert "unavailable" in response.json()["error"].lower()


def test_qdrant_error_returns_503():
    mock_agent = MagicMock()
    mock_agent.process_text.return_value = AgentResult.failure(
        error=QdrantConnectionError("Qdrant unreachable")
    )
    client = _client_with_resume_override(mock_agent)
    response = client.post("/resume/analyze", json={"text": VALID_RESUME_TEXT})
    assert response.status_code == 503


def test_rate_limit_error_returns_429():
    mock_agent = MagicMock()
    mock_agent.process_text.return_value = AgentResult.failure(
        error=ProviderRateLimitError("Rate limited")
    )
    client = _client_with_resume_override(mock_agent)
    response = client.post("/resume/analyze", json={"text": VALID_RESUME_TEXT})
    assert response.status_code == 429


def test_extraction_error_returns_422():
    mock_agent = MagicMock()
    mock_agent.process_text.return_value = AgentResult.failure(
        error=ExtractionError("not json")
    )
    client = _client_with_resume_override(mock_agent)
    response = client.post("/resume/analyze", json={"text": VALID_RESUME_TEXT})
    assert response.status_code == 422


def test_invalid_request_body_returns_422():
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: MagicMock()
    app.dependency_overrides[get_embedding_provider] = lambda: MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: MagicMock()
    client = TestClient(app, raise_server_exceptions=False)

    # Send an invalid JSON body (missing required 'text' field)
    response = client.post("/resume/analyze", json={"wrong_field": "data"})
    # FastAPI natively returns 422 for schema validation failures
    assert response.status_code == 422

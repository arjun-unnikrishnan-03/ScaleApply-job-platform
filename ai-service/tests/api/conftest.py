"""
Shared fixtures and utilities for API tests.
All live providers and vector stores are replaced with mocks via dependency_overrides.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies.providers import get_llm_provider
from api.dependencies.vectorstores import get_embedding_provider, get_vector_store
from api.dependencies.queue import get_queue_service, get_event_publisher
from core.result import AgentResult


# ── Minimal mock LLM provider ─────────────────────────────────────────────────

class MockLLMProvider:
    """Stub LLM provider that returns a preset response string."""

    def __init__(self, response_content: str = "{}") -> None:
        self.response_content = response_content

    def generate(self, prompt: str, config=None):
        class FakeResponse:
            content = self.response_content
            model = "mock"
            input_tokens = 0
            output_tokens = 0
        return FakeResponse()

    def get_model_name(self) -> str:
        return "mock"


# ── Minimal mock embedding provider ──────────────────────────────────────────

class MockEmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def get_dimension(self) -> int:
        return 3


# ── Minimal mock vector store ─────────────────────────────────────────────────

class MockVectorStore:
    def upsert_documents(self, documents, embeddings) -> None:
        pass

    def search(self, query_vector, limit=5):
        return []

    def upsert_chunks(self, chunks, embeddings) -> None:
        pass

    def search_chunks(self, query_vector, limit=5):
        return []

    def delete(self, document_id: str) -> bool:
        return True

    def get_document(self, document_id: str):
        return None


# ── Minimal mock Redis Queue and Publisher ─────────────────────────────────────

class MockQueueService:
    def __init__(self) -> None:
        self.results = {}
        self.streams = {}

    def ping(self) -> bool:
        return True

    def publish(self, stream: str, event) -> str:
        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(event)
        return "12345-0"

    def get_queue_depth(self, stream: str) -> int:
        return len(self.streams.get(stream, []))

    def create_consumer_group(self, stream: str, group: str) -> bool:
        return True

    def ack_message(self, stream: str, group: str, message_id: str) -> None:
        pass

    def set_result(self, correlation_id: str, status: str, result=None, error=None, attempts=1) -> None:
        self.results[correlation_id] = {
            "correlation_id": correlation_id,
            "status": status,
            "result": result,
            "error": error,
            "attempts": attempts,
            "updated_at": "2024-01-01T00:00:00Z"
        }

    def get_result(self, correlation_id: str):
        return self.results.get(correlation_id)


class MockEventPublisher:
    def __init__(self, queue_service) -> None:
        self.queue_service = queue_service

    def publish_event(self, stream: str, event) -> str:
        return self.queue_service.publish(stream, event)


@pytest.fixture()
def mock_queue_service():
    return MockQueueService()


@pytest.fixture()
def app_with_mocks(mock_queue_service):
    """Create a FastAPI app with all external dependencies overridden."""
    app = create_app()
    mock_provider = MockLLMProvider()
    mock_embed = MockEmbeddingProvider()
    mock_store = MockVectorStore()
    mock_publisher = MockEventPublisher(mock_queue_service)

    app.dependency_overrides[get_llm_provider] = lambda: mock_provider
    app.dependency_overrides[get_embedding_provider] = lambda: mock_embed
    app.dependency_overrides[get_vector_store] = lambda: mock_store
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service
    app.dependency_overrides[get_event_publisher] = lambda: mock_publisher

    return app


@pytest.fixture()
def client(app_with_mocks):
    """TestClient with all mocks wired in."""
    return TestClient(app_with_mocks, raise_server_exceptions=False)

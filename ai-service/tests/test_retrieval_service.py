"""
Tests for RetrievalService.
"""

import pytest

from core.exceptions import ProviderError
from services.retrieval_service import RetrievalService
from models.knowledge_document import KnowledgeDocument
from vectorstores.base import VectorStore
from embeddings.base import EmbeddingProvider

class MockEmbeddingProvider(EmbeddingProvider):
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]
    def get_dimension(self) -> int:
        return 3

class MockVectorStore(VectorStore):
    def upsert_documents(self, documents: list[KnowledgeDocument], embeddings: list[list[float]]) -> None:
        pass
    def search(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeDocument]:
        return [
            KnowledgeDocument(title="Test", category="Test", content="Content 1")
        ][:limit]
    def upsert_chunks(self, chunks: list, embeddings: list[list[float]]) -> None:
        pass
    def search_chunks(self, query_vector: list[float], limit: int = 5) -> list:
        return []
    def delete(self, document_id: str) -> bool:
        return True
    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        return None

@pytest.fixture
def mock_provider():
    return MockEmbeddingProvider()

@pytest.fixture
def mock_store():
    return MockVectorStore()

@pytest.fixture
def service(mock_provider, mock_store):
    return RetrievalService(provider=mock_provider, vector_store=mock_store)

def test_retrieval_service_success(service):
    result = service.retrieve("query")
    assert result.is_success is True
    res = result.unwrap()
    assert res.query == "query"
    assert len(res.documents) == 1
    assert res.documents[0].title == "Test"
    assert len(res.scores) == 1

def test_retrieval_service_empty_query(service):
    result = service.retrieve("")
    assert result.is_success is True
    res = result.unwrap()
    assert res.query == ""
    assert len(res.documents) == 0

def test_retrieval_service_provider_error(service, monkeypatch):
    def mock_embed(text):
        raise ProviderError("Embed fail")
    monkeypatch.setattr(service._provider, "embed_text", mock_embed)
    
    result = service.retrieve("query")
    assert result.is_success is False
    assert isinstance(result.error, ProviderError)

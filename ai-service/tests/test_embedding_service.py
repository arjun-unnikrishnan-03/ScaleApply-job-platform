"""
Tests for EmbeddingService.
"""

import pytest

from core.exceptions import ProviderError
from models.knowledge_document import KnowledgeDocument
from services.embedding_service import EmbeddingService
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
    def __init__(self):
        self.store = {}
        self.upsert_called = False
    def upsert_documents(self, documents: list[KnowledgeDocument], embeddings: list[list[float]]) -> None:
        self.upsert_called = True
        for doc in documents:
            self.store[doc.id] = doc
    def search(self, query_vector: list[float], limit: int = 5) -> list[KnowledgeDocument]:
        return []
    def upsert_chunks(self, chunks: list, embeddings: list[list[float]]) -> None:
        pass
    def search_chunks(self, query_vector: list[float], limit: int = 5) -> list:
        return []
    def delete(self, document_id: str) -> bool:
        return True
    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        return self.store.get(document_id)

@pytest.fixture
def mock_provider():
    return MockEmbeddingProvider()

@pytest.fixture
def mock_store():
    return MockVectorStore()

@pytest.fixture
def service(mock_provider, mock_store):
    return EmbeddingService(provider=mock_provider, vector_store=mock_store)

@pytest.fixture
def sample_doc():
    return KnowledgeDocument(
        title="Test",
        category="Test",
        content="This is a test document."
    )

def test_process_and_store_success(service, sample_doc, mock_store):
    result = service.process_and_store(sample_doc)
    assert result.is_success is True
    assert result.unwrap() is True
    
    # Verify it made it into the store
    stored_doc = mock_store.get_document(sample_doc.id)
    assert stored_doc is not None
    assert stored_doc.title == "Test"

def test_process_and_store_provider_failure(service, sample_doc, monkeypatch):
    def mock_embed_text(text):
        raise ProviderError("API down")
        
    monkeypatch.setattr(service._provider, "embed_text", mock_embed_text)
    
    result = service.process_and_store(sample_doc)
    assert result.is_success is False
    assert isinstance(result.error, ProviderError)

def test_process_batch_success(service):
    docs = [
        KnowledgeDocument(title="Test1", category="Test", content="Content 1"),
        KnowledgeDocument(title="Test2", category="Test", content="Content 2")
    ]
    
    result = service.process_batch(docs)
    assert result.is_success is True
    assert result.unwrap() == 2
    
def test_process_batch_empty_list(service):
    result = service.process_batch([])
    assert result.is_success is True
    assert result.unwrap() == 0

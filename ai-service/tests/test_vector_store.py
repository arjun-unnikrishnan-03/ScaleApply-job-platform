"""
Tests for QdrantVectorStore.
"""

from unittest.mock import MagicMock, patch

import pytest
from qdrant_client.http import exceptions as qdrant_http_exceptions
from qdrant_client.http.models import PointStruct, ScoredPoint, UpdateResult

from core.exceptions import QdrantConnectionError, QdrantSearchError
from models.knowledge_document import KnowledgeDocument
from vectorstores.qdrant_store import QdrantVectorStore

@pytest.fixture
def mock_qdrant_client():
    with patch("vectorstores.qdrant_store.QdrantClient") as mock:
        client_instance = mock.return_value
        
        # Mock get_collections to simulate collection already exists
        col_mock = MagicMock()
        col_mock.name = "knowledge_base"
        collections_response = MagicMock()
        collections_response.collections = [col_mock]
        client_instance.get_collections.return_value = collections_response
        
        yield client_instance

@pytest.fixture
def store(mock_qdrant_client):
    return QdrantVectorStore()

def test_initialization_creates_collection(mock_qdrant_client):
    # Simulate collection does not exist
    empty_response = MagicMock()
    empty_response.collections = []
    mock_qdrant_client.get_collections.return_value = empty_response
    
    store = QdrantVectorStore()
    
    mock_qdrant_client.create_collection.assert_called_once()
    args, kwargs = mock_qdrant_client.create_collection.call_args
    assert kwargs["collection_name"] == "knowledge_base"

def test_upsert_mismatched_lengths(store):
    with pytest.raises(ValueError):
        store.upsert_documents([KnowledgeDocument(title="A", category="B", content="C")], [])

def test_upsert_success(store, mock_qdrant_client):
    doc = KnowledgeDocument(title="A", category="B", content="C", id="doc-123")
    
    store.upsert_documents([doc], [[0.1, 0.2]])
    
    mock_qdrant_client.upsert.assert_called_once()
    args, kwargs = mock_qdrant_client.upsert.call_args
    points = kwargs["points"]
    assert len(points) == 1
    assert points[0].id == "doc-123"
    assert points[0].vector == [0.1, 0.2]
    assert points[0].payload["title"] == "A"

def test_search_success(store, mock_qdrant_client):
    scored_point = MagicMock(spec=ScoredPoint)
    scored_point.payload = {
        "id": "doc-456",
        "title": "Title",
        "category": "Cat",
        "content": "Content",
        "tags": []
    }
    
    mock_qdrant_client.search.return_value = [scored_point]
    
    results = store.search([0.1, 0.2])
    
    assert len(results) == 1
    assert isinstance(results[0], KnowledgeDocument)
    assert results[0].title == "Title"

def test_search_qdrant_error(store, mock_qdrant_client):
    # Raise a proper qdrant_client unexpected response error with status_code
    mock_qdrant_client.search.side_effect = qdrant_http_exceptions.UnexpectedResponse(
        status_code=500, reason_phrase="Error", content=b"", headers={}
    )
    
    with pytest.raises(QdrantSearchError):
        store.search([0.1])

def test_delete_success(store, mock_qdrant_client):
    mock_response = MagicMock(spec=UpdateResult)
    mock_response.status = "completed"
    mock_qdrant_client.delete.return_value = mock_response
    
    success = store.delete("doc-1")
    assert success is True

def test_get_document_found(store, mock_qdrant_client):
    point = MagicMock()
    point.payload = {
        "id": "doc-789",
        "title": "Found",
        "category": "Test",
        "content": "Content",
        "tags": []
    }
    mock_qdrant_client.retrieve.return_value = [point]
    
    doc = store.get_document("doc-789")
    assert doc is not None
    assert doc.title == "Found"

def test_get_document_not_found(store, mock_qdrant_client):
    mock_qdrant_client.retrieve.return_value = []
    
    doc = store.get_document("doc-000")
    assert doc is None

"""
Tests for KnowledgeIndexer.
"""

import pytest

from core.exceptions import ProviderError
from core.result import AgentResult
from models.indexing_report import IndexingReport
from models.knowledge_document import KnowledgeDocument
from indexers.knowledge_indexer import KnowledgeIndexer

class MockLoader:
    def __init__(self, docs_to_return=None):
        self.docs_to_return = docs_to_return or []
        self.called = False

    def load_documents(self):
        self.called = True
        return self.docs_to_return

class MockEmbeddingService:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.processed_docs = []

    def process_batch(self, documents):
        if self.should_fail:
            return AgentResult.failure(error=ProviderError("Simulated failure"))
        self.processed_docs.extend(documents)
        return AgentResult.success(len(documents))


def test_indexer_success():
    docs = [
        KnowledgeDocument(title="Doc1", category="Cat", content="Content"),
        KnowledgeDocument(title="Doc2", category="Cat", content="Content")
    ]
    loader = MockLoader(docs_to_return=docs)
    service = MockEmbeddingService()
    indexer = KnowledgeIndexer(loader, service)
    
    result = indexer.index_all()
    assert result.is_success is True
    
    report = result.unwrap()
    assert isinstance(report, IndexingReport)
    assert report.total_documents == 2
    assert report.indexed_documents == 2
    assert report.failed_documents == 0
    assert report.success_rate == 100.0
    
    assert loader.called is True
    assert len(service.processed_docs) == 2

def test_indexer_no_documents():
    loader = MockLoader(docs_to_return=[])
    service = MockEmbeddingService()
    indexer = KnowledgeIndexer(loader, service)
    
    result = indexer.index_all()
    assert result.is_success is True
    
    report = result.unwrap()
    assert report.total_documents == 0
    assert report.indexed_documents == 0
    assert report.success_rate == 100.0
    assert len(service.processed_docs) == 0

def test_indexer_service_failure():
    docs = [KnowledgeDocument(title="Doc1", category="Cat", content="Content")]
    loader = MockLoader(docs_to_return=docs)
    service = MockEmbeddingService(should_fail=True)
    indexer = KnowledgeIndexer(loader, service)
    
    result = indexer.index_all()
    assert result.is_success is True  # Indexer returns a report, not a failure monad
    
    report = result.unwrap()
    assert report.total_documents == 1
    assert report.indexed_documents == 0
    assert report.failed_documents == 1
    assert report.success_rate == 0.0

def test_indexer_exception_propagation():
    class CrashLoader:
        def load_documents(self):
            raise ValueError("Loader crashed")
            
    indexer = KnowledgeIndexer(CrashLoader(), MockEmbeddingService())
    result = indexer.index_all()
    
    assert result.is_success is False
    assert "Loader crashed" in str(result.error)

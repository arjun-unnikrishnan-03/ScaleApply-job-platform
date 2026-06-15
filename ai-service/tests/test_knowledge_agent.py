"""
Tests for KnowledgeAgent.
"""

import json

import pytest

from agents.knowledge_agent import KnowledgeAgent
from core.exceptions import ExtractionError, ProviderError, ValidationError
from core.result import AgentResult
from models.knowledge_response import KnowledgeResponse
from models.retrieval_result import RetrievalResult
from models.knowledge_document import KnowledgeDocument
from tests.conftest import MockLLMProvider

SAMPLE_KNOWLEDGE_DICT = {
    "answer": "Docker uses containers to virtualize OS-level processes.",
    "sources": ["docker.md"],
    "confidence": 0.95
}

class MockRetrievalService:
    def __init__(self, should_fail=False, empty=False):
        self.should_fail = should_fail
        self.empty = empty

    def retrieve(self, query: str):
        if self.should_fail:
            return AgentResult.failure(error=RuntimeError("Retrieval broke"))
        if self.empty:
            res = RetrievalResult(query=query, documents=[], scores=[])
            return AgentResult.success(res)
            
        doc = KnowledgeDocument(title="Docker", category="skills", content="Docker containers", source="docker.md")
        res = RetrievalResult(query=query, documents=[doc], scores=[1.0])
        return AgentResult.success(res)


@pytest.fixture
def mock_knowledge_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_KNOWLEDGE_DICT)


@pytest.fixture
def failing_provider() -> MockLLMProvider:
    return MockLLMProvider(should_fail=True)

def test_knowledge_agent_success(mock_knowledge_provider):
    retrieval_service = MockRetrievalService()
    agent = KnowledgeAgent(mock_knowledge_provider, retrieval_service)
    
    result = agent.ask("What is Docker?")
    assert result.is_success is True
    
    response = result.unwrap()
    assert isinstance(response, KnowledgeResponse)
    assert response.confidence == 0.95
    assert len(response.sources) == 1

def test_knowledge_agent_retrieval_failure(mock_knowledge_provider):
    retrieval_service = MockRetrievalService(should_fail=True)
    agent = KnowledgeAgent(mock_knowledge_provider, retrieval_service)
    
    result = agent.ask("What is Docker?")
    assert result.is_success is False
    assert "Retrieval broke" in str(result.error)

def test_knowledge_agent_provider_failure(failing_provider):
    retrieval_service = MockRetrievalService()
    agent = KnowledgeAgent(failing_provider, retrieval_service)
    
    result = agent.ask("What is Docker?")
    assert result.is_success is False
    assert isinstance(result.error, ProviderError)

def test_knowledge_agent_empty_retrieval(mock_knowledge_provider):
    retrieval_service = MockRetrievalService(empty=True)
    agent = KnowledgeAgent(mock_knowledge_provider, retrieval_service)
    
    # Prompt should handle NO CONTEXT DOCUMENTS gracefully, LLM is mocked though
    result = agent.ask("What is Docker?")
    assert result.is_success is True
    assert result.unwrap().confidence == 0.95

def test_knowledge_agent_invalid_json():
    provider = MockLLMProvider(raw_response="Not JSON")
    retrieval_service = MockRetrievalService()
    agent = KnowledgeAgent(provider, retrieval_service)
    
    result = agent.ask("Q")
    assert result.is_success is False
    assert isinstance(result.error, ExtractionError)

def test_knowledge_agent_validation_error():
    invalid_data = {**SAMPLE_KNOWLEDGE_DICT, "confidence": 5.0} # invalid range
    provider = MockLLMProvider(response_json=invalid_data)
    retrieval_service = MockRetrievalService()
    agent = KnowledgeAgent(provider, retrieval_service)
    
    result = agent.ask("Q")
    assert result.is_success is False
    assert isinstance(result.error, ValidationError)

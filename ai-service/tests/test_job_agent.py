"""
Tests for JobAgent.
"""

from __future__ import annotations

import json

import pytest

from agents.job_agent import JobAgent
from core.exceptions import (
    EmptyDocumentError,
    ExtractionError,
    ParseError,
    ProviderError,
    ValidationError,
)
from models.job_description import JobDescription
from tests.conftest import MockLLMProvider
from tests.test_job_description import SAMPLE_JOB_DICT

SAMPLE_JOB_TEXT = """
Senior Python Backend Engineer
TechCorp - Remote
Full Time

We are looking for a Senior Backend Engineer to join our fast-growing startup.
You must have 5+ years of experience with Python and FastAPI.

Responsibilities:
- Design APIs
- Mentor junior devs

Requirements:
- Python
- FastAPI
- PostgreSQL
- Experience with AWS and Docker preferred.
"""

@pytest.fixture
def mock_job_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_JOB_DICT)

@pytest.fixture
def failing_provider() -> MockLLMProvider:
    return MockLLMProvider(should_fail=True)

def make_job_agent(provider: MockLLMProvider) -> JobAgent:
    return JobAgent(provider=provider, min_job_words=10)


class TestJobAgentSuccess:
    def test_process_text_returns_success_result(self, mock_job_provider):
        agent = make_job_agent(mock_job_provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success is True
        assert isinstance(result.value, JobDescription)

    def test_job_has_correct_title(self, mock_job_provider):
        agent = make_job_agent(mock_job_provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.value.title == "Senior Python Backend Engineer"

    def test_unwrap_returns_job_description(self, mock_job_provider):
        agent = make_job_agent(mock_job_provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        job = result.unwrap()
        assert isinstance(job, JobDescription)

    def test_json_in_markdown_fences_is_handled(self):
        raw = f"```json\n{json.dumps(SAMPLE_JOB_DICT)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_job_agent(provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success


class TestJobAgentEmptyInput:
    def test_empty_string_returns_failure(self, mock_job_provider):
        agent = make_job_agent(mock_job_provider)
        result = agent.process_text("")
        assert result.is_success is False
        assert isinstance(result.error, EmptyDocumentError)

    def test_too_short_returns_failure(self, mock_job_provider):
        agent = make_job_agent(mock_job_provider)
        result = agent.process_text("Backend Engineer needed")
        assert result.is_success is False
        assert isinstance(result.error, EmptyDocumentError)


class TestJobAgentProviderFailure:
    def test_provider_failure_returns_failure_result(self, failing_provider):
        agent = make_job_agent(failing_provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)


class TestJobAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(self):
        provider = MockLLMProvider(raw_response="No JSON here.")
        agent = make_job_agent(provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)

    def test_not_a_job_description_returns_parse_error(self):
        provider = MockLLMProvider(raw_response='{"title": "UNKNOWN", "error": "Not a job description"}')
        agent = make_job_agent(provider)
        result = agent.process_text("This is a cake recipe.")
        assert result.is_success is False
        assert isinstance(result.error, ParseError)


class TestJobAgentValidation:
    def test_missing_required_field_returns_validation_error(self):
        incomplete = {k: v for k, v in SAMPLE_JOB_DICT.items() if k != "title"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_job_agent(provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_empty_skills_returns_validation_error(self):
        invalid = {**SAMPLE_JOB_DICT, "required_skills": [], "technologies": []}
        provider = MockLLMProvider(response_json=invalid)
        agent = make_job_agent(provider)
        result = agent.process_text(SAMPLE_JOB_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

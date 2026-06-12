"""
Tests for ATSAgent.
"""

from __future__ import annotations

import json

import pytest

from agents.ats_agent import ATSAgent
from core.exceptions import (
    ExtractionError,
    ProviderError,
    ValidationError,
)
from models.ats_result import ATSResult
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from tests.conftest import MockLLMProvider
from tests.test_ats_result import SAMPLE_ATS_DICT
from tests.conftest import SAMPLE_CANDIDATE_JSON
from tests.test_job_description import SAMPLE_JOB_DICT


@pytest.fixture
def mock_ats_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_ATS_DICT)


@pytest.fixture
def failing_provider() -> MockLLMProvider:
    return MockLLMProvider(should_fail=True)


@pytest.fixture
def sample_candidate() -> CandidateProfile:
    return CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)


@pytest.fixture
def sample_job() -> JobDescription:
    return JobDescription.model_validate(SAMPLE_JOB_DICT)


def make_ats_agent(provider: MockLLMProvider) -> ATSAgent:
    return ATSAgent(provider=provider)


class TestATSAgentSuccess:
    def test_evaluate_returns_success_result(self, mock_ats_provider, sample_candidate, sample_job):
        agent = make_ats_agent(mock_ats_provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success is True
        assert isinstance(result.value, ATSResult)

    def test_result_contains_metadata(self, mock_ats_provider, sample_candidate, sample_job):
        agent = make_ats_agent(mock_ats_provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.metadata["candidate_name"] == sample_candidate.full_name
        assert result.metadata["job_title"] == sample_job.title

    def test_unwrap_returns_ats_result(self, mock_ats_provider, sample_candidate, sample_job):
        agent = make_ats_agent(mock_ats_provider)
        result = agent.evaluate(sample_candidate, sample_job)
        ats_result = result.unwrap()
        assert isinstance(ats_result, ATSResult)

    def test_json_in_markdown_fences_is_handled(self, sample_candidate, sample_job):
        raw = f"```json\n{json.dumps(SAMPLE_ATS_DICT)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_ats_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success


class TestATSAgentProviderFailure:
    def test_provider_failure_returns_failure_result(self, failing_provider, sample_candidate, sample_job):
        agent = make_ats_agent(failing_provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)


class TestATSAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(self, sample_candidate, sample_job):
        provider = MockLLMProvider(raw_response="No JSON here.")
        agent = make_ats_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)


class TestATSAgentValidation:
    def test_missing_required_field_returns_validation_error(self, sample_candidate, sample_job):
        incomplete = {k: v for k, v in SAMPLE_ATS_DICT.items() if k != "score"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_ats_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_invalid_score_returns_validation_error(self, sample_candidate, sample_job):
        invalid = {**SAMPLE_ATS_DICT, "score": 110.0}
        provider = MockLLMProvider(response_json=invalid)
        agent = make_ats_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

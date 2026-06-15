"""
Tests for SkillGapAgent.
"""

from __future__ import annotations

import json

import pytest

from agents.skill_gap_agent import SkillGapAgent
from core.exceptions import (
    ExtractionError,
    ProviderError,
    ValidationError,
)
from models.skill_gap_result import SkillGapResult
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from tests.conftest import MockLLMProvider
from tests.test_skill_gap_result import SAMPLE_SKILL_GAP_DICT
from tests.conftest import SAMPLE_CANDIDATE_JSON
from tests.test_job_description import SAMPLE_JOB_DICT
from tests.test_ats_result import SAMPLE_ATS_DICT


@pytest.fixture
def mock_skill_gap_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_SKILL_GAP_DICT)


@pytest.fixture
def failing_provider() -> MockLLMProvider:
    return MockLLMProvider(should_fail=True)


@pytest.fixture
def sample_candidate() -> CandidateProfile:
    return CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)


@pytest.fixture
def sample_job() -> JobDescription:
    return JobDescription.model_validate(SAMPLE_JOB_DICT)


@pytest.fixture
def sample_ats() -> ATSResult:
    return ATSResult.model_validate(SAMPLE_ATS_DICT)


def make_skill_gap_agent(provider: MockLLMProvider) -> SkillGapAgent:
    return SkillGapAgent(provider=provider)


class TestSkillGapAgentSuccess:
    def test_analyze_returns_success_result(self, mock_skill_gap_provider, sample_candidate, sample_job, sample_ats):
        agent = make_skill_gap_agent(mock_skill_gap_provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success is True
        assert isinstance(result.value, SkillGapResult)

    def test_result_contains_metadata(self, mock_skill_gap_provider, sample_candidate, sample_job, sample_ats):
        agent = make_skill_gap_agent(mock_skill_gap_provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.metadata["candidate_name"] == sample_candidate.full_name
        assert result.metadata["job_title"] == sample_job.title

    def test_unwrap_returns_skill_gap_result(self, mock_skill_gap_provider, sample_candidate, sample_job, sample_ats):
        agent = make_skill_gap_agent(mock_skill_gap_provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        gap_result = result.unwrap()
        assert isinstance(gap_result, SkillGapResult)

    def test_json_in_markdown_fences_is_handled(self, sample_candidate, sample_job, sample_ats):
        raw = f"```json\n{json.dumps(SAMPLE_SKILL_GAP_DICT)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_skill_gap_agent(provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success


class TestSkillGapAgentProviderFailure:
    def test_provider_failure_returns_failure_result(self, failing_provider, sample_candidate, sample_job, sample_ats):
        agent = make_skill_gap_agent(failing_provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)


class TestSkillGapAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(self, sample_candidate, sample_job, sample_ats):
        provider = MockLLMProvider(raw_response="No JSON here.")
        agent = make_skill_gap_agent(provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)


class TestSkillGapAgentValidation:
    def test_missing_required_field_returns_validation_error(self, sample_candidate, sample_job, sample_ats):
        incomplete = {k: v for k, v in SAMPLE_SKILL_GAP_DICT.items() if k != "match_percentage"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_skill_gap_agent(provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_invalid_weeks_returns_validation_error(self, sample_candidate, sample_job, sample_ats):
        invalid = {**SAMPLE_SKILL_GAP_DICT, "estimated_learning_weeks": -5.0}
        provider = MockLLMProvider(response_json=invalid)
        agent = make_skill_gap_agent(provider)
        result = agent.analyze(sample_candidate, sample_job, sample_ats)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

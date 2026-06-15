"""
Tests for RecruiterAgent.
"""

from __future__ import annotations

import json

import pytest

from agents.recruiter_agent import RecruiterAgent
from core.exceptions import (
    ExtractionError,
    ProviderError,
    ValidationError,
)
from models.recruiter_decision import RecruiterDecision
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from models.interview_result import InterviewResult
from tests.conftest import MockLLMProvider
from tests.test_recruiter_decision import SAMPLE_RECRUITER_DICT
from tests.conftest import SAMPLE_CANDIDATE_JSON
from tests.test_job_description import SAMPLE_JOB_DICT
from tests.test_ats_result import SAMPLE_ATS_DICT
from tests.test_skill_gap_result import SAMPLE_SKILL_GAP_DICT
from tests.test_interview_result import SAMPLE_INTERVIEW_DICT


@pytest.fixture
def mock_recruiter_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_RECRUITER_DICT)


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


@pytest.fixture
def sample_skill_gap() -> SkillGapResult:
    return SkillGapResult.model_validate(SAMPLE_SKILL_GAP_DICT)


@pytest.fixture
def sample_interview() -> InterviewResult:
    return InterviewResult.model_validate(SAMPLE_INTERVIEW_DICT)


def make_recruiter_agent(provider: MockLLMProvider) -> RecruiterAgent:
    return RecruiterAgent(provider=provider)


class TestRecruiterAgentSuccess:
    def test_evaluate_returns_success_result(
        self, mock_recruiter_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        agent = make_recruiter_agent(mock_recruiter_provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success is True
        assert isinstance(result.value, RecruiterDecision)

    def test_result_contains_metadata(
        self, mock_recruiter_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        agent = make_recruiter_agent(mock_recruiter_provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.metadata["candidate_name"] == sample_candidate.full_name
        assert result.metadata["job_title"] == sample_job.title

    def test_unwrap_returns_recruiter_decision(
        self, mock_recruiter_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        agent = make_recruiter_agent(mock_recruiter_provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        decision = result.unwrap()
        assert isinstance(decision, RecruiterDecision)

    def test_json_in_markdown_fences_is_handled(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        raw = f"```json\n{json.dumps(SAMPLE_RECRUITER_DICT)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_recruiter_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success


class TestRecruiterAgentProviderFailure:
    def test_provider_failure_returns_failure_result(
        self, failing_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        agent = make_recruiter_agent(failing_provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)


class TestRecruiterAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        provider = MockLLMProvider(raw_response="No JSON here.")
        agent = make_recruiter_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)


class TestRecruiterAgentValidation:
    def test_missing_required_field_returns_validation_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        incomplete = {k: v for k, v in SAMPLE_RECRUITER_DICT.items() if k != "summary"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_recruiter_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_invalid_recommendation_returns_validation_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview
    ):
        invalid = {**SAMPLE_RECRUITER_DICT, "recommendation": "Maybe Hire"}
        provider = MockLLMProvider(response_json=invalid)
        agent = make_recruiter_agent(provider)
        result = agent.evaluate(sample_candidate, sample_job, sample_ats, sample_skill_gap, sample_interview)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

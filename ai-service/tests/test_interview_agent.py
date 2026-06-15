"""
Tests for InterviewAgent.
"""

from __future__ import annotations

import json

import pytest

from agents.interview_agent import InterviewAgent
from core.exceptions import (
    ExtractionError,
    ProviderError,
    ValidationError,
)
from models.interview_result import InterviewResult
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from tests.conftest import MockLLMProvider
from tests.test_interview_result import SAMPLE_INTERVIEW_DICT
from tests.conftest import SAMPLE_CANDIDATE_JSON
from tests.test_job_description import SAMPLE_JOB_DICT
from tests.test_ats_result import SAMPLE_ATS_DICT
from tests.test_skill_gap_result import SAMPLE_SKILL_GAP_DICT


@pytest.fixture
def mock_interview_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_INTERVIEW_DICT)


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


def make_interview_agent(provider: MockLLMProvider) -> InterviewAgent:
    return InterviewAgent(provider=provider)


class TestInterviewAgentSuccess:
    def test_generate_returns_success_result(
        self, mock_interview_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        agent = make_interview_agent(mock_interview_provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success is True
        assert isinstance(result.value, InterviewResult)

    def test_result_contains_metadata(
        self, mock_interview_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        agent = make_interview_agent(mock_interview_provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.metadata["candidate_name"] == sample_candidate.full_name
        assert result.metadata["job_title"] == sample_job.title

    def test_unwrap_returns_interview_result(
        self, mock_interview_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        agent = make_interview_agent(mock_interview_provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        interview_result = result.unwrap()
        assert isinstance(interview_result, InterviewResult)

    def test_json_in_markdown_fences_is_handled(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        raw = f"```json\n{json.dumps(SAMPLE_INTERVIEW_DICT)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_interview_agent(provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success


class TestInterviewAgentProviderFailure:
    def test_provider_failure_returns_failure_result(
        self, failing_provider, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        agent = make_interview_agent(failing_provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)


class TestInterviewAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        provider = MockLLMProvider(raw_response="No JSON here.")
        agent = make_interview_agent(provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)


class TestInterviewAgentValidation:
    def test_missing_required_field_returns_validation_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        incomplete = {k: v for k, v in SAMPLE_INTERVIEW_DICT.items() if k != "explanation"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_interview_agent(provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_empty_rubric_returns_validation_error(
        self, sample_candidate, sample_job, sample_ats, sample_skill_gap
    ):
        invalid = {**SAMPLE_INTERVIEW_DICT, "evaluation_rubric": []}
        provider = MockLLMProvider(response_json=invalid)
        agent = make_interview_agent(provider)
        result = agent.generate(sample_candidate, sample_job, sample_ats, sample_skill_gap)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

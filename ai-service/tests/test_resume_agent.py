"""
Tests for ResumeAgent.

All tests use MockLLMProvider — no network calls, no API keys required.
Tests cover success paths, all error branches, and edge cases.
"""

from __future__ import annotations

import json

import pytest

from agents.resume_agent import ResumeAgent
from core.exceptions import (
    EmptyDocumentError,
    ExtractionError,
    ProviderError,
    ValidationError,
)
from core.result import AgentResult
from models.candidate_profile import CandidateProfile
from tests.conftest import (
    MockLLMProvider,
    SAMPLE_CANDIDATE_JSON,
    SAMPLE_RESUME_TEXT,
    MINIMAL_RESUME_TEXT,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_agent(provider: MockLLMProvider) -> ResumeAgent:
    return ResumeAgent(provider=provider)


# ── Success path ──────────────────────────────────────────────────────────────

class TestResumeAgentSuccess:
    def test_process_text_returns_success_result(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)

        assert result.is_success is True
        assert isinstance(result.value, CandidateProfile)

    def test_profile_has_correct_name(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.value.full_name == "Alice Johnson"

    def test_profile_has_experience(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert len(result.value.experience) == 2

    def test_result_contains_metadata(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT, source_name="test.pdf")
        assert result.metadata["source_file"] == "test.pdf"
        assert result.metadata["model"] == "mock-model-v1"
        assert result.metadata["prompt_version"] is not None

    def test_provider_receives_resume_text_in_prompt(self, mock_provider):
        agent = make_agent(mock_provider)
        agent.process_text(SAMPLE_RESUME_TEXT)
        # The provider's last prompt should contain the resume text
        assert "Alice Johnson" in mock_provider.last_prompt

    def test_provider_called_exactly_once(self, mock_provider):
        agent = make_agent(mock_provider)
        agent.process_text(SAMPLE_RESUME_TEXT)
        assert mock_provider.call_count == 1

    def test_result_bool_is_true_on_success(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert bool(result) is True

    def test_unwrap_returns_profile(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        profile = result.unwrap()
        assert isinstance(profile, CandidateProfile)

    def test_json_in_markdown_fences_is_handled(self):
        """LLMs sometimes wrap JSON in ```json ... ``` — must be stripped."""
        raw = f"```json\n{json.dumps(SAMPLE_CANDIDATE_JSON)}\n```"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success
        assert result.value.full_name == "Alice Johnson"

    def test_json_with_surrounding_text_is_handled(self):
        """LLMs sometimes add preamble text before the JSON."""
        raw = f"Sure! Here is the extracted data:\n{json.dumps(SAMPLE_CANDIDATE_JSON)}\nHope this helps!"
        provider = MockLLMProvider(raw_response=raw)
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success


# ── Empty document errors ─────────────────────────────────────────────────────

class TestResumeAgentEmptyInput:
    def test_empty_string_returns_failure(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text("")
        assert result.is_success is False
        assert isinstance(result.error, EmptyDocumentError)

    def test_whitespace_only_returns_failure(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text("   \n\n\t  ")
        assert result.is_success is False

    def test_too_short_returns_failure(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text("John Doe")
        assert result.is_success is False
        assert isinstance(result.error, EmptyDocumentError)

    def test_result_bool_is_false_on_failure(self, mock_provider):
        agent = make_agent(mock_provider)
        result = agent.process_text("")
        assert bool(result) is False


# ── Provider errors ───────────────────────────────────────────────────────────

class TestResumeAgentProviderFailure:
    def test_provider_failure_returns_failure_result(self, failing_provider):
        agent = make_agent(failing_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ProviderError)

    def test_failure_result_has_metadata(self, failing_provider):
        agent = make_agent(failing_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT, source_name="test.pdf")
        assert result.metadata.get("source_file") == "test.pdf"

    def test_unwrap_on_failure_raises(self, failing_provider):
        agent = make_agent(failing_provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        with pytest.raises(ProviderError):
            result.unwrap()


# ── JSON extraction errors ────────────────────────────────────────────────────

class TestResumeAgentExtractionErrors:
    def test_non_json_response_returns_extraction_error(self):
        provider = MockLLMProvider(raw_response="I'm sorry, I cannot extract data.")
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ExtractionError)

    def test_empty_json_object_fails_validation(self):
        """An empty JSON {} will fail because full_name is required."""
        provider = MockLLMProvider(raw_response="{}")
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_not_a_resume_returns_parse_error(self):
        from core.exceptions import ParseError
        provider = MockLLMProvider(raw_response='{"full_name": "UNKNOWN", "error": "Not a resume"}')
        agent = make_agent(provider)
        result = agent.process_text("This is a recipe for chocolate cake." * 20)
        assert result.is_success is False
        assert isinstance(result.error, ParseError)


# ── Validation errors ─────────────────────────────────────────────────────────

class TestResumeAgentValidation:
    def test_missing_required_field_returns_validation_error(self):
        """full_name is required — a response without it must fail."""
        incomplete = {k: v for k, v in SAMPLE_CANDIDATE_JSON.items() if k != "full_name"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success is False
        assert isinstance(result.error, ValidationError)

    def test_validation_error_has_pydantic_details(self):
        incomplete = {k: v for k, v in SAMPLE_CANDIDATE_JSON.items() if k != "full_name"}
        provider = MockLLMProvider(response_json=incomplete)
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert "pydantic_errors" in result.error.details


# ── Dependency injection ──────────────────────────────────────────────────────

class TestResumeAgentDI:
    def test_agent_accepts_any_llm_provider(self):
        """Verify the agent truly only depends on the LLMProvider interface."""
        import json as _json
        from providers.base import ProviderResponse

        class AnotherMockProvider(MockLLMProvider):
            def get_model_name(self) -> str:
                return "another-provider-v2"

            def generate(self, prompt, config=None):
                self.call_count += 1
                self.last_prompt = prompt
                return ProviderResponse(
                    content=_json.dumps(SAMPLE_CANDIDATE_JSON),
                    model=self.get_model_name(),   # Use own model name
                    input_tokens=50,
                    output_tokens=100,
                    finish_reason="stop",
                )

        provider = AnotherMockProvider(response_json=SAMPLE_CANDIDATE_JSON)
        agent = make_agent(provider)
        result = agent.process_text(SAMPLE_RESUME_TEXT)
        assert result.is_success
        assert result.metadata["model"] == "another-provider-v2"

    def test_agent_uses_injected_provider_not_global(self):
        """Two agents with different providers must use their own."""
        provider_a = MockLLMProvider(response_json={**SAMPLE_CANDIDATE_JSON, "full_name": "Agent A"})
        provider_b = MockLLMProvider(response_json={**SAMPLE_CANDIDATE_JSON, "full_name": "Agent B"})

        agent_a = ResumeAgent(provider=provider_a)
        agent_b = ResumeAgent(provider=provider_b)

        result_a = agent_a.process_text(SAMPLE_RESUME_TEXT)
        result_b = agent_b.process_text(SAMPLE_RESUME_TEXT)

        assert result_a.value.full_name == "Agent A"
        assert result_b.value.full_name == "Agent B"

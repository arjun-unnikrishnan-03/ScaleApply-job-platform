"""
Shared test fixtures and mock implementations.

MockLLMProvider is a drop-in replacement for any real LLM in tests.
It returns configurable responses without network calls.
"""

from __future__ import annotations

import json

import pytest

from providers.base import GenerationConfig, LLMProvider, ProviderResponse
from core.exceptions import ProviderError

# Shared data lives in demo_data.py (no pytest import) so main.py can
# also use it without pulling in pytest as a runtime dependency.
from demo_data import SAMPLE_CANDIDATE_JSON, SAMPLE_RESUME_TEXT

MINIMAL_RESUME_TEXT = """
John Doe
john@example.com
Software Developer with 3 years of Python and Django experience.
Worked at ACME Corp as Backend Engineer from 2020 to 2023.
Computer Science degree from State University, graduated 2019.
"""


# ── Mock Provider ─────────────────────────────────────────────────────────────

class MockLLMProvider(LLMProvider):
    """
    Deterministic mock LLM provider for unit testing.

    Configure the response before each test:
        provider = MockLLMProvider(response_json={...})
    """

    def __init__(
        self,
        response_json: dict | None = None,
        raw_response: str | None = None,
        should_fail: bool = False,
        fail_with: type[ProviderError] | None = None,
    ) -> None:
        self._response_json = response_json
        self._raw_response = raw_response
        self._should_fail = should_fail
        self._fail_with = fail_with or ProviderError
        self.call_count = 0
        self.last_prompt: str | None = None

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> ProviderResponse:
        self.call_count += 1
        self.last_prompt = prompt

        if self._should_fail:
            raise self._fail_with("Mock provider failure")

        content = self._raw_response or json.dumps(self._response_json or {})
        return ProviderResponse(
            content=content,
            model="mock-model-v1",
            input_tokens=100,
            output_tokens=200,
            finish_reason="stop",
        )

    def get_model_name(self) -> str:
        return "mock-model-v1"

    def health_check(self) -> bool:
        return not self._should_fail


# ── pytest Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_provider() -> MockLLMProvider:
    return MockLLMProvider(response_json=SAMPLE_CANDIDATE_JSON)


@pytest.fixture
def failing_provider() -> MockLLMProvider:
    return MockLLMProvider(should_fail=True)


@pytest.fixture
def sample_candidate_json() -> dict:
    return SAMPLE_CANDIDATE_JSON.copy()


@pytest.fixture
def sample_resume_text() -> str:
    return SAMPLE_RESUME_TEXT


@pytest.fixture
def minimal_resume_text() -> str:
    return MINIMAL_RESUME_TEXT

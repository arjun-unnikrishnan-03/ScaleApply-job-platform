"""
Tests for ProviderFactory registry.
"""

from __future__ import annotations

import pytest

from providers.base import GenerationConfig, LLMProvider, ProviderResponse
from providers.factory import ProviderFactory
from core.exceptions import ProviderNotFoundError


class AnotherMockProvider(LLMProvider):
    def generate(self, prompt, config=None):
        return ProviderResponse(content='{}', model='another-mock')

    def get_model_name(self):
        return 'another-mock'

    def health_check(self):
        return True


class TestProviderFactory:
    def test_gemini_is_registered(self):
        assert "gemini" in ProviderFactory.available_providers()

    def test_available_providers_returns_list(self):
        providers = ProviderFactory.available_providers()
        assert isinstance(providers, list)
        assert len(providers) >= 1

    def test_unknown_provider_raises_not_found(self):
        with pytest.raises(ProviderNotFoundError) as exc_info:
            ProviderFactory.create("nonexistent_llm_xyz")
        assert "nonexistent_llm_xyz" in str(exc_info.value)

    def test_register_custom_provider(self):
        ProviderFactory.register("another_mock", AnotherMockProvider)
        assert "another_mock" in ProviderFactory.available_providers()

    def test_create_registered_custom_provider(self):
        ProviderFactory.register("another_mock2", AnotherMockProvider)
        provider = ProviderFactory.create("another_mock2")
        assert isinstance(provider, AnotherMockProvider)

    def test_provider_name_is_case_insensitive(self):
        ProviderFactory.register("CaseMockProvider", AnotherMockProvider)
        provider = ProviderFactory.create("casemockprovider")
        assert isinstance(provider, AnotherMockProvider)

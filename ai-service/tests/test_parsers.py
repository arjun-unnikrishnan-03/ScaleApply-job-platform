"""
Tests for ResumeExtractionPrompt.
"""

from __future__ import annotations

import pytest

from prompts.resume_prompt import ResumeExtractionPrompt


class TestResumeExtractionPrompt:
    def setup_method(self):
        self.prompt = ResumeExtractionPrompt()

    def test_version_is_semantic(self):
        parts = self.prompt.version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_description_is_non_empty(self):
        assert len(self.prompt.description) > 10

    def test_build_includes_resume_text(self):
        result = self.prompt.build(resume_text="Alice Johnson, Software Engineer")
        assert "Alice Johnson" in result

    def test_build_includes_json_schema(self):
        result = self.prompt.build(resume_text="John Doe, Developer")
        assert "full_name" in result
        assert "technical_skills" in result

    def test_build_raises_on_empty_text(self):
        with pytest.raises(ValueError):
            self.prompt.build(resume_text="")

    def test_build_truncates_long_text(self):
        long_text = "A" * 15_000
        result = self.prompt.build(resume_text=long_text)
        assert "TRUNCATED" in result
        # Prompt should be significantly shorter than original
        assert len(result) < len(long_text)

    def test_system_instruction_present(self):
        instruction = self.prompt.get_system_instruction()
        assert "JSON" in instruction
        assert len(instruction) > 50

    def test_build_user_content_does_not_repeat_system(self):
        user_content = self.prompt.build_user_content("John Doe at ACME Corp")
        system = self.prompt.get_system_instruction()
        # The opening system lines should not be in user_content
        assert "CRITICAL RULES:" not in user_content

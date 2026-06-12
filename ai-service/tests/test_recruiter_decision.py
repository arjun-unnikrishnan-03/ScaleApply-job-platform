"""
Tests for RecruiterDecision domain model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.recruiter_decision import RecruiterDecision

# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_RECRUITER_DICT = {
    "recommendation": "Consider",
    "confidence": 0.85,
    "strengths": ["Strong backend experience", "Python expertise"],
    "risks": ["Lacks Docker experience", "Short tenure at previous job"],
    "interview_focus_areas": ["Containerization knowledge", "Mentorship skills"],
    "summary": "Candidate is a strong backend developer but needs to prove they can learn DevOps quickly.",
    "reasoning": "The ATS score is solid, but the skill gap analysis highlights a missing critical requirement (Docker). We should consider them, provided they perform well on the DevOps portion of the interview."
}

class TestRecruiterDecision:
    def test_full_construction_from_dict(self):
        result = RecruiterDecision.model_validate(SAMPLE_RECRUITER_DICT)
        assert result.recommendation == "Consider"
        assert result.confidence == 0.85
        assert len(result.strengths) == 2
        assert len(result.risks) == 2
        assert len(result.interview_focus_areas) == 2

    def test_invalid_recommendation_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RecruiterDecision.model_validate({**SAMPLE_RECRUITER_DICT, "recommendation": "Maybe"})

    def test_invalid_confidence_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RecruiterDecision.model_validate({**SAMPLE_RECRUITER_DICT, "confidence": 1.5})
            
        with pytest.raises(ValidationError):
            RecruiterDecision.model_validate({**SAMPLE_RECRUITER_DICT, "confidence": -0.5})

    def test_empty_summary_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RecruiterDecision.model_validate({**SAMPLE_RECRUITER_DICT, "summary": ""})

    def test_empty_reasoning_raises_validation_error(self):
        with pytest.raises(ValidationError):
            RecruiterDecision.model_validate({**SAMPLE_RECRUITER_DICT, "reasoning": ""})

    def test_list_deduplication(self):
        data = {**SAMPLE_RECRUITER_DICT}
        data["strengths"] = ["Python", "python", "FASTAPI  ", "FastAPI"]
        result = RecruiterDecision.model_validate(data)
        assert len(result.strengths) == 2
        assert result.strengths[0] == "Python"
        assert result.strengths[1] == "FASTAPI"

    def test_frozen_prevents_mutation(self):
        result = RecruiterDecision.model_validate(SAMPLE_RECRUITER_DICT)
        with pytest.raises(Exception):
            result.confidence = 0.90  # type: ignore

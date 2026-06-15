"""
Tests for ATSResult domain model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.ats_result import ATSResult

# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_ATS_DICT = {
    "score": 85.5,
    "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_skills": ["Docker", "Kubernetes"],
    "strengths": ["Strong backend experience", "Relevant tech stack"],
    "weaknesses": ["No DevOps experience"],
    "recommendations": ["Proceed to technical interview"],
    "explanation": "The candidate has strong Python and FastAPI skills matching the core requirements, but lacks containerization experience."
}

class TestATSResult:
    def test_full_construction_from_dict(self):
        result = ATSResult.model_validate(SAMPLE_ATS_DICT)
        assert result.score == 85.5
        assert len(result.matched_skills) == 3
        assert result.is_strong_match(threshold=80.0) is True

    def test_invalid_score_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ATSResult.model_validate({**SAMPLE_ATS_DICT, "score": 150.0})

        with pytest.raises(ValidationError):
            ATSResult.model_validate({**SAMPLE_ATS_DICT, "score": -10.0})

    def test_empty_explanation_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ATSResult.model_validate({**SAMPLE_ATS_DICT, "explanation": ""})

    def test_list_deduplication(self):
        data = {
            **SAMPLE_ATS_DICT,
            "matched_skills": ["Python", "python", "FASTAPI  ", "FastAPI"]
        }
        result = ATSResult.model_validate(data)
        assert len(result.matched_skills) == 2
        # Verify it preserved original casing of the first encountered item
        assert result.matched_skills[0] == "Python"
        assert result.matched_skills[1] == "FASTAPI"

    def test_frozen_prevents_mutation(self):
        result = ATSResult.model_validate(SAMPLE_ATS_DICT)
        with pytest.raises(Exception):
            result.score = 90.0  # type: ignore

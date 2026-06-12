"""
Tests for SkillGapResult domain model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.skill_gap_result import SkillGapResult

# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_SKILL_GAP_DICT = {
    "match_percentage": 85.0,
    "missing_skills": ["Docker", "Kubernetes"],
    "priority_order": ["Docker", "Kubernetes"],
    "estimated_learning_weeks": 4.5,
    "strengths": ["Python", "FastAPI"],
    "roadmap": [
        {
            "skill_name": "Docker",
            "actionable_advice": "Take an introductory Docker course and containerize a FastAPI app.",
            "estimated_weeks": 1.5
        },
        {
            "skill_name": "Kubernetes",
            "actionable_advice": "Learn K8s basics and deploy the containerized app.",
            "estimated_weeks": 3.0
        }
    ],
    "explanation": "Candidate is strong in backend dev but lacks required DevOps skills."
}

class TestSkillGapResult:
    def test_full_construction_from_dict(self):
        result = SkillGapResult.model_validate(SAMPLE_SKILL_GAP_DICT)
        assert result.match_percentage == 85.0
        assert len(result.missing_skills) == 2
        assert len(result.roadmap) == 2
        assert result.estimated_learning_weeks == 4.5

    def test_invalid_percentage_raises_validation_error(self):
        with pytest.raises(ValidationError):
            SkillGapResult.model_validate({**SAMPLE_SKILL_GAP_DICT, "match_percentage": 150.0})

        with pytest.raises(ValidationError):
            SkillGapResult.model_validate({**SAMPLE_SKILL_GAP_DICT, "match_percentage": -10.0})

    def test_invalid_weeks_raises_validation_error(self):
        with pytest.raises(ValidationError):
            SkillGapResult.model_validate({**SAMPLE_SKILL_GAP_DICT, "estimated_learning_weeks": -1.0})

    def test_empty_explanation_raises_validation_error(self):
        with pytest.raises(ValidationError):
            SkillGapResult.model_validate({**SAMPLE_SKILL_GAP_DICT, "explanation": ""})

    def test_list_deduplication(self):
        data = {
            **SAMPLE_SKILL_GAP_DICT,
            "missing_skills": ["Docker", "docker", "KUBERNETES  ", "Kubernetes"]
        }
        result = SkillGapResult.model_validate(data)
        assert len(result.missing_skills) == 2
        # Verify it preserved original casing of the first encountered item
        assert result.missing_skills[0] == "Docker"
        assert result.missing_skills[1] == "KUBERNETES"

    def test_roadmap_deduplication(self):
        data = {
            **SAMPLE_SKILL_GAP_DICT,
            "roadmap": [
                {
                    "skill_name": "Docker",
                    "actionable_advice": "Learn Docker",
                    "estimated_weeks": 1.0
                },
                {
                    "skill_name": "docker",
                    "actionable_advice": "Duplicate step",
                    "estimated_weeks": 2.0
                }
            ]
        }
        result = SkillGapResult.model_validate(data)
        assert len(result.roadmap) == 1
        assert result.roadmap[0].skill_name == "Docker"

    def test_frozen_prevents_mutation(self):
        result = SkillGapResult.model_validate(SAMPLE_SKILL_GAP_DICT)
        with pytest.raises(Exception):
            result.match_percentage = 90.0  # type: ignore

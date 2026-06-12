"""
Tests for InterviewResult domain model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.interview_result import InterviewResult

# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_INTERVIEW_DICT = {
    "technical_questions": [
        {
            "question": "Can you explain how you optimized the PostgreSQL database at TechCorp?",
            "category": "Technical",
            "difficulty": "Medium",
            "reason": "Candidate has PostgreSQL experience and the job requires database optimization."
        }
    ],
    "project_questions": [
        {
            "question": "In your OpenResume project, how did you handle NLP extraction?",
            "category": "Project",
            "difficulty": "Hard",
            "reason": "Probing depth of knowledge in their mentioned side project."
        }
    ],
    "behavioral_questions": [
        {
            "question": "Tell me about a time you had to mentor a junior developer.",
            "category": "Behavioral",
            "difficulty": "Easy",
            "reason": "Job description mentions mentoring junior devs as a responsibility."
        }
    ],
    "weak_area_questions": [
        {
            "question": "How would you approach containerizing an application with Docker, given you haven't used it professionally?",
            "category": "Weak Area",
            "difficulty": "Medium",
            "reason": "Docker is a required skill but missing from the candidate's profile."
        }
    ],
    "evaluation_rubric": [
        {
            "criteria": "Database Optimization Knowledge",
            "passing_score_description": "Can clearly articulate indexing and query planning."
        }
    ],
    "explanation": "This interview focuses on diving deep into backend architecture while testing the candidate's learning agility for missing DevOps skills."
}

class TestInterviewResult:
    def test_full_construction_from_dict(self):
        result = InterviewResult.model_validate(SAMPLE_INTERVIEW_DICT)
        assert len(result.technical_questions) == 1
        assert len(result.project_questions) == 1
        assert len(result.behavioral_questions) == 1
        assert len(result.weak_area_questions) == 1
        assert len(result.evaluation_rubric) == 1

    def test_invalid_difficulty_raises_validation_error(self):
        data = {**SAMPLE_INTERVIEW_DICT}
        data["technical_questions"] = [
            {
                "question": "Test",
                "category": "Technical",
                "difficulty": "Super Hard",  # Invalid
                "reason": "Test"
            }
        ]
        with pytest.raises(ValidationError):
            InterviewResult.model_validate(data)

    def test_empty_rubric_raises_validation_error(self):
        data = {**SAMPLE_INTERVIEW_DICT, "evaluation_rubric": []}
        with pytest.raises(ValidationError):
            InterviewResult.model_validate(data)

    def test_empty_explanation_raises_validation_error(self):
        with pytest.raises(ValidationError):
            InterviewResult.model_validate({**SAMPLE_INTERVIEW_DICT, "explanation": ""})

    def test_question_deduplication(self):
        data = {**SAMPLE_INTERVIEW_DICT}
        data["technical_questions"] = [
            {
                "question": "How do you optimize DBs?",
                "category": "Technical",
                "difficulty": "Easy",
                "reason": "Test"
            },
            {
                "question": "How do you optimize DBs?",
                "category": "Technical",
                "difficulty": "Hard",
                "reason": "Duplicate text"
            }
        ]
        result = InterviewResult.model_validate(data)
        assert len(result.technical_questions) == 1
        assert result.technical_questions[0].difficulty == "Easy"

    def test_frozen_prevents_mutation(self):
        result = InterviewResult.model_validate(SAMPLE_INTERVIEW_DICT)
        with pytest.raises(Exception):
            result.explanation = "New text"  # type: ignore

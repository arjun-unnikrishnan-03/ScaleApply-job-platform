"""
Tests for the main domain routers: resume, job, ats, skill-gap, interview, recruiter.
All agents are tested via dependency_overrides — no live API calls occur.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies.agents import (
    get_ats_agent,
    get_interview_agent,
    get_job_agent,
    get_recruiter_agent,
    get_resume_agent,
    get_skill_gap_agent,
)
from api.dependencies.providers import get_llm_provider
from api.dependencies.vectorstores import get_embedding_provider, get_vector_store
from core.result import AgentResult
from core.exceptions import GeminiProviderError, QdrantConnectionError

# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_CANDIDATE_PROFILE = {
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone": None,
    "linkedin_url": None,
    "github_url": None,
    "location": None,
    "portfolio_url": None,
    "professional_summary": "Experienced engineer",
    "technical_skills": ["Python", "FastAPI"],
    "soft_skills": [],
    "languages": [],
    "experience": [],
    "education": [],
    "projects": [],
    "certifications": [],
    "years_of_experience": None,
    "extracted_at": "2024-01-01T00:00:00+00:00",
    "source_file": "inline",
}

VALID_JOB_DESCRIPTION = {
    "title": "Backend Engineer",
    "department": None,
    "company_name": "TechCorp",
    "location": None,
    "remote_policy": None,
    "employment_type": None,
    "experience_required": None,
    "required_skills": ["Python"],
    "preferred_skills": [],
    "technologies": [],
    "responsibilities": ["Build stuff"],
    "qualifications": ["BS in CS"],
    "benefits": [],
    "salary_range": None,
    "summary": "Build APIs",
    "source_name": "inline",
    "extracted_at": "2024-01-01T00:00:00+00:00",
}

VALID_ATS_RESULT = {
    "candidate_name": "Jane Doe",
    "job_title": "Backend Engineer",
    "score": 80,
    "matched_skills": ["Python"],
    "missing_skills": [],
    "strengths": ["Strong Python skills"],
    "weaknesses": [],
    "recommendations": ["Great match"],
    "explanation": "Strong candidate with matching skills.",
    "evaluated_at": "2024-01-01T00:00:00+00:00",
}

VALID_SKILL_GAP_RESULT = {
    "candidate_name": "Jane Doe",
    "job_title": "Backend Engineer",
    "match_percentage": 80,
    "estimated_learning_weeks": 4,
    "missing_skills": [],
    "priority_order": [],
    "strengths": ["Python"],
    "roadmap": [],
    "explanation": "Ready soon.",
    "analyzed_at": "2024-01-01T00:00:00+00:00",
}

VALID_INTERVIEW_RESULT = {
    "candidate_name": "Jane Doe",
    "job_title": "Backend Engineer",
    "technical_questions": [{
        "question": "Explain async in Python.",
        "category": "Technical",
        "difficulty": "Medium",
        "reason": "Core async knowledge required",
    }],
    "project_questions": [],
    "behavioral_questions": [],
    "weak_area_questions": [],
    "evaluation_rubric": [{
        "criteria": "Technical depth: assess Python and async knowledge",
        "passing_score_description": "Must answer 3 of 5 technical questions correctly."
    }],
    "explanation": "Personalized interview kit.",
    "generated_at": "2024-01-01T00:00:00+00:00",
}


def _make_client_with_agent_override(agent_dep, mock_agent):
    """Create a test client with a specific agent dependency overridden."""
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: MagicMock()
    app.dependency_overrides[get_embedding_provider] = lambda: MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: MagicMock()
    app.dependency_overrides[agent_dep] = lambda: mock_agent
    return TestClient(app, raise_server_exceptions=False)


# ── Resume tests ─────────────────────────────────────────────────────────────

def test_resume_analyze_success():
    from models.candidate_profile import CandidateProfile
    mock_agent = MagicMock()
    profile = CandidateProfile.model_validate(VALID_CANDIDATE_PROFILE)
    mock_agent.process_text.return_value = AgentResult.success(profile)

    client = _make_client_with_agent_override(get_resume_agent, mock_agent)
    response = client.post("/resume/analyze", json={"text": "Jane Doe, experienced software engineer with 5 years in Python and FastAPI development."})

    assert response.status_code == 200
    body = response.json()
    assert "profile" in body
    assert body["profile"]["full_name"] == "Jane Doe"


def test_resume_analyze_too_short():
    app = create_app()
    app.dependency_overrides[get_llm_provider] = lambda: MagicMock()
    app.dependency_overrides[get_embedding_provider] = lambda: MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: MagicMock()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/resume/analyze", json={"text": "short"})
    # FastAPI returns 422 for request-level pydantic validation (min_length)
    assert response.status_code == 422


def test_resume_analyze_provider_failure():
    mock_agent = MagicMock()
    mock_agent.process_text.return_value = AgentResult.failure(
        error=GeminiProviderError("API down")
    )
    client = _make_client_with_agent_override(get_resume_agent, mock_agent)
    response = client.post(
        "/resume/analyze",
        json={"text": "Jane Doe, experienced software engineer with 5 years in Python and FastAPI development."},
    )
    assert response.status_code == 503


# ── Job tests ────────────────────────────────────────────────────────────────

def test_job_analyze_success():
    from models.job_description import JobDescription
    mock_agent = MagicMock()
    job = JobDescription.model_validate(VALID_JOB_DESCRIPTION)
    mock_agent.process_text.return_value = AgentResult.success(job)

    client = _make_client_with_agent_override(get_job_agent, mock_agent)
    response = client.post("/job/analyze", json={"text": "Senior Backend Engineer needed at TechCorp to build scalable REST APIs using Python and FastAPI."})

    assert response.status_code == 200
    body = response.json()
    assert "job_description" in body


# ── ATS tests ────────────────────────────────────────────────────────────────

def test_ats_analyze_success():
    from models.ats_result import ATSResult
    mock_agent = MagicMock()
    ats = ATSResult.model_validate(VALID_ATS_RESULT)
    mock_agent.evaluate.return_value = AgentResult.success(ats)

    client = _make_client_with_agent_override(get_ats_agent, mock_agent)
    response = client.post("/ats/analyze", json={
        "candidate_profile": VALID_CANDIDATE_PROFILE,
        "job_description": VALID_JOB_DESCRIPTION,
    })

    assert response.status_code == 200
    body = response.json()
    assert "ats_result" in body
    assert body["ats_result"]["score"] == 80


def test_ats_analyze_vector_store_error():
    mock_agent = MagicMock()
    mock_agent.evaluate.return_value = AgentResult.failure(
        error=QdrantConnectionError("unreachable")
    )
    client = _make_client_with_agent_override(get_ats_agent, mock_agent)
    response = client.post("/ats/analyze", json={
        "candidate_profile": VALID_CANDIDATE_PROFILE,
        "job_description": VALID_JOB_DESCRIPTION,
    })
    assert response.status_code == 503


# ── Skill gap tests ───────────────────────────────────────────────────────────

def test_skill_gap_analyze_success():
    from models.skill_gap_result import SkillGapResult
    mock_agent = MagicMock()
    skill_gap = SkillGapResult.model_validate(VALID_SKILL_GAP_RESULT)
    mock_agent.analyze.return_value = AgentResult.success(skill_gap)

    client = _make_client_with_agent_override(get_skill_gap_agent, mock_agent)
    response = client.post("/skill-gap/analyze", json={
        "candidate_profile": VALID_CANDIDATE_PROFILE,
        "job_description": VALID_JOB_DESCRIPTION,
        "ats_result": VALID_ATS_RESULT,
    })

    assert response.status_code == 200
    body = response.json()
    assert "skill_gap_result" in body


# ── Interview tests ───────────────────────────────────────────────────────────

def test_interview_generate_success():
    from models.interview_result import InterviewResult
    mock_agent = MagicMock()
    interview = InterviewResult.model_validate(VALID_INTERVIEW_RESULT)
    mock_agent.generate.return_value = AgentResult.success(interview)

    client = _make_client_with_agent_override(get_interview_agent, mock_agent)
    response = client.post("/interview/generate", json={
        "candidate_profile": VALID_CANDIDATE_PROFILE,
        "job_description": VALID_JOB_DESCRIPTION,
        "ats_result": VALID_ATS_RESULT,
        "skill_gap_result": VALID_SKILL_GAP_RESULT,
    })

    assert response.status_code == 200
    body = response.json()
    assert "interview_result" in body


# ── Recruiter tests ───────────────────────────────────────────────────────────

def test_recruiter_evaluate_success():
    from models.recruiter_decision import RecruiterDecision
    VALID_DECISION = {
        "candidate_name": "Jane Doe",
        "job_title": "Backend Engineer",
        "recommendation": "StrongHire",
        "confidence": 0.9,
        "summary": "Excellent candidate",
        "reasoning": "Strong Python skills",
        "strengths": ["Python", "FastAPI"],
        "risks": [],
        "interview_focus_areas": ["System design"],
        "decided_at": "2024-01-01T00:00:00+00:00",
    }
    mock_agent = MagicMock()
    decision = RecruiterDecision.model_validate(VALID_DECISION)
    mock_agent.evaluate.return_value = AgentResult.success(decision)

    client = _make_client_with_agent_override(get_recruiter_agent, mock_agent)
    response = client.post("/recruiter/evaluate", json={
        "candidate_profile": VALID_CANDIDATE_PROFILE,
        "job_description": VALID_JOB_DESCRIPTION,
        "ats_result": VALID_ATS_RESULT,
        "skill_gap_result": VALID_SKILL_GAP_RESULT,
        "interview_result": VALID_INTERVIEW_RESULT,
    })

    assert response.status_code == 200
    body = response.json()
    assert "recruiter_decision" in body
    assert body["recruiter_decision"]["recommendation"] == "StrongHire"

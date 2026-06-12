"""
Tests for JobDescription domain model.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.job_description import (
    EmploymentType,
    ExperienceLevel,
    ExperienceRequirement,
    JobDescription,
    SalaryRange,
)

# ── Sample Data ───────────────────────────────────────────────────────────────

SAMPLE_JOB_DICT = {
    "title": "Senior Python Backend Engineer",
    "department": "Engineering",
    "company_name": "TechCorp",
    "location": "San Francisco, CA",
    "remote_policy": "remote",
    "employment_type": "full_time",
    "experience_required": {
        "min_years": 5.0,
        "max_years": None,
        "level": "senior",
        "raw_text": "5+ years of experience"
    },
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "preferred_skills": ["Docker", "Kubernetes", "Redis"],
    "technologies": ["AWS", "GitHub Actions"],
    "responsibilities": ["Design APIs", "Mentor junior devs"],
    "qualifications": ["BS in Computer Science"],
    "benefits": [{"name": "Health Insurance", "description": "Full coverage"}],
    "salary_range": {
        "min_amount": 140000.0,
        "max_amount": 180000.0,
        "currency": "USD",
        "period": "annual",
        "raw_text": "$140k - $180k"
    },
    "summary": "Join our fast-growing startup to build scalable backend systems."
}


class TestExperienceRequirement:
    def test_valid_min_max(self):
        req = ExperienceRequirement(min_years=3.0, max_years=5.0)
        assert req.max_years == 5.0

    def test_max_less_than_min_raises(self):
        with pytest.raises(ValidationError):
            ExperienceRequirement(min_years=5.0, max_years=3.0)


class TestSalaryRange:
    def test_valid_range(self):
        sal = SalaryRange(min_amount=100000.0, max_amount=120000.0)
        assert sal.max_amount == 120000.0

    def test_max_less_than_min_raises(self):
        with pytest.raises(ValidationError):
            SalaryRange(min_amount=120000.0, max_amount=100000.0)


class TestJobDescription:
    def test_full_construction_from_dict(self):
        job = JobDescription.model_validate(SAMPLE_JOB_DICT)
        assert job.title == "Senior Python Backend Engineer"
        assert job.employment_type == EmploymentType.FULL_TIME.value
        assert job.experience_required.min_years == 5.0

    def test_employment_type_normalization(self):
        data = {**SAMPLE_JOB_DICT, "employment_type": "Contract/Temp"}
        job = JobDescription.model_validate(data)
        assert job.employment_type == EmploymentType.UNKNOWN.value

        data = {**SAMPLE_JOB_DICT, "employment_type": "part time"}
        job = JobDescription.model_validate(data)
        assert job.employment_type == EmploymentType.PART_TIME.value

    def test_skill_deduplication_and_splitting(self):
        data = {
            **SAMPLE_JOB_DICT,
            "required_skills": ["Python", "Python", "FastAPI, PostgreSQL", "redis"],
            "technologies": []
        }
        job = JobDescription.model_validate(data)
        assert "Python" in job.required_skills
        assert "FastAPI" in job.required_skills
        assert "PostgreSQL" in job.required_skills
        assert "redis" in job.required_skills
        assert len(job.required_skills) == 4

    def test_technology_normalization(self):
        data = {
            **SAMPLE_JOB_DICT,
            "technologies": ["AWS, Docker", "aws", "DOCKER"],
            "required_skills": []
        }
        job = JobDescription.model_validate(data)
        assert "AWS" in job.technologies
        assert "Docker" in job.technologies
        assert len(job.technologies) == 2

    def test_required_skills_and_tech_not_empty(self):
        # Setting both to empty should raise ValidationError
        data = {**SAMPLE_JOB_DICT, "required_skills": [], "technologies": []}
        with pytest.raises(ValidationError):
            JobDescription.model_validate(data)

    def test_all_required_technologies_helper(self):
        data = {
            **SAMPLE_JOB_DICT,
            "required_skills": ["Python", "Java"],
            "technologies": ["AWS", "Docker", "python"]
        }
        job = JobDescription.model_validate(data)
        techs = job.all_required_technologies()
        assert "python" in techs
        assert "java" in techs
        assert "aws" in techs
        assert "docker" in techs
        assert len(techs) == 4

    def test_is_remote_helper(self):
        data = {**SAMPLE_JOB_DICT, "remote_policy": "Hybrid Remote"}
        job = JobDescription.model_validate(data)
        assert job.is_remote() is True

        data["remote_policy"] = "On-site"
        job = JobDescription.model_validate(data)
        assert job.is_remote() is False

        data["remote_policy"] = None
        job = JobDescription.model_validate(data)
        assert job.is_remote() is False

    def test_seniority_level_helper(self):
        job = JobDescription.model_validate(SAMPLE_JOB_DICT)
        assert job.seniority_level() == ExperienceLevel.SENIOR

        data = {**SAMPLE_JOB_DICT, "experience_required": None}
        job2 = JobDescription.model_validate(data)
        assert job2.seniority_level() == ExperienceLevel.UNKNOWN

    def test_frozen_prevents_mutation(self):
        job = JobDescription.model_validate(SAMPLE_JOB_DICT)
        with pytest.raises(Exception):
            job.title = "New Title"  # type: ignore

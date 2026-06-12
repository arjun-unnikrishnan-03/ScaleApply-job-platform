"""
Tests for CandidateProfile domain model.

Validates field validators, semantic constraints,
and computed helper methods.
"""

from __future__ import annotations

import pytest
from datetime import date
from pydantic import ValidationError

from models.candidate_profile import (
    CandidateProfile,
    DateRange,
    Education,
    Experience,
    Project,
    Certification,
)
from tests.conftest import SAMPLE_CANDIDATE_JSON


class TestDateRange:
    def test_valid_open_range(self):
        dr = DateRange(start_date=date(2020, 1, 1), end_date=None)
        assert dr.end_date is None

    def test_valid_closed_range(self):
        dr = DateRange(start_date=date(2018, 1, 1), end_date=date(2022, 6, 1))
        assert dr.end_date == date(2022, 6, 1)

    def test_end_before_start_raises(self):
        with pytest.raises(ValidationError):
            DateRange(start_date=date(2022, 1, 1), end_date=date(2020, 1, 1))


class TestEducation:
    def test_gpa_from_string(self):
        edu = Education(
            institution="MIT",
            degree="BSc",
            field_of_study="CS",
            graduation_year=2020,
            gpa="3.9/4.0",  # Common string format from resumes
        )
        assert edu.gpa == 3.9

    def test_invalid_gpa_returns_none(self):
        edu = Education(
            institution="MIT",
            degree="BSc",
            gpa="N/A",  # Cannot parse → gracefully null
        )
        assert edu.gpa is None

    def test_gpa_range_validation(self):
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="BSc", gpa=5.0)  # Exceeds 4.0


class TestExperience:
    def test_deduplicated_skills(self):
        exp = Experience(
            company="ACME",
            title="Engineer",
            technologies_used=["Python", "python", "PYTHON", "Django"],
        )
        assert exp.technologies_used == ["Python", "Django"]

    def test_empty_responsibilities_ok(self):
        exp = Experience(company="ACME", title="SWE")
        assert exp.responsibilities == []


class TestProject:
    def test_url_without_scheme_gets_https(self):
        proj = Project(name="MyApp", url="github.com/user/repo")
        assert proj.url == "https://github.com/user/repo"

    def test_invalid_url_becomes_none(self):
        proj = Project(name="MyApp", url="not_a_url_at_all")
        assert proj.url is None


class TestCandidateProfile:
    def test_full_construction_from_dict(self):
        profile = CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)
        assert profile.full_name == "Alice Johnson"
        assert profile.email == "alice@example.com"
        assert len(profile.experience) == 2
        assert len(profile.education) == 1
        assert len(profile.certifications) == 1

    def test_email_normalization(self):
        data = {**SAMPLE_CANDIDATE_JSON, "email": "  ALICE@EXAMPLE.COM  "}
        profile = CandidateProfile.model_validate(data)
        assert profile.email == "alice@example.com"

    def test_invalid_email_becomes_none(self):
        data = {**SAMPLE_CANDIDATE_JSON, "email": "not-an-email"}
        profile = CandidateProfile.model_validate(data)
        assert profile.email is None

    def test_skill_deduplication(self):
        data = {
            **SAMPLE_CANDIDATE_JSON,
            "technical_skills": ["Python", "python", "PYTHON", "Django", "django"],
        }
        profile = CandidateProfile.model_validate(data)
        assert "Python" in profile.technical_skills
        assert len([s for s in profile.technical_skills if s.lower() == "python"]) == 1

    def test_years_of_experience_string_coercion(self):
        data = {**SAMPLE_CANDIDATE_JSON, "years_of_experience": "7+ years"}
        profile = CandidateProfile.model_validate(data)
        assert profile.years_of_experience == 7.0

    def test_is_complete_true_for_full_profile(self):
        profile = CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)
        assert profile.is_complete() is True

    def test_is_complete_false_for_name_only(self):
        profile = CandidateProfile.model_validate({
            "full_name": "Ghost Candidate"
        })
        assert profile.is_complete() is False

    def test_total_technologies_aggregates_across_sections(self):
        profile = CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)
        techs = profile.total_technologies()
        assert "python" in techs
        assert "fastapi" in techs
        assert "node.js" in techs  # from experience technologies_used
        assert "spacy" in techs   # from project technologies

    def test_frozen_prevents_mutation(self):
        profile = CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)
        with pytest.raises(Exception):  # frozen=True raises ValidationError or FrozenInstanceError
            profile.full_name = "Hacker"  # type: ignore

    def test_summary_dict_keys(self):
        profile = CandidateProfile.model_validate(SAMPLE_CANDIDATE_JSON)
        summary = profile.summary_dict()
        assert "full_name" in summary
        assert "is_complete" in summary
        assert "technical_skills_count" in summary

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            CandidateProfile.model_validate({
                **SAMPLE_CANDIDATE_JSON,
                "unknown_field": "should_fail",
            })

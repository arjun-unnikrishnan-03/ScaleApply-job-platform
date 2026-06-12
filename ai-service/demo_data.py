"""
demo_data.py — standalone sample data for main.py demo mode.

Kept separate from tests/conftest.py so main.py does NOT
transitively import pytest (which is a dev-only dependency).
"""

SAMPLE_CANDIDATE_JSON = {
    "full_name": "Alice Johnson",
    "email": "alice@example.com",
    "phone": "+1-555-0100",
    "linkedin_url": "https://linkedin.com/in/alicejohnson",
    "github_url": "https://github.com/alicejohnson",
    "location": "San Francisco, CA",
    "portfolio_url": None,
    "professional_summary": "Senior software engineer with 7 years of backend experience.",
    "years_of_experience": 7.0,
    "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
    "soft_skills": ["Leadership", "Communication", "Problem Solving"],
    "languages": ["English", "Spanish"],
    "experience": [
        {
            "company": "TechCorp Inc.",
            "title": "Senior Software Engineer",
            "location": "San Francisco, CA",
            "duration": {"start_date": "2020-06-01", "end_date": None},
            "responsibilities": [
                "Led design of microservices architecture serving 5M users",
                "Reduced API latency by 40% through Redis caching",
            ],
            "technologies_used": ["Python", "FastAPI", "Redis", "PostgreSQL"],
        },
        {
            "company": "StartupXYZ",
            "title": "Software Engineer",
            "location": "Remote",
            "duration": {"start_date": "2017-01-01", "end_date": "2020-05-01"},
            "responsibilities": ["Built RESTful APIs", "Implemented CI/CD pipelines"],
            "technologies_used": ["Node.js", "MongoDB", "Jenkins"],
        },
    ],
    "education": [
        {
            "institution": "UC Berkeley",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "graduation_year": 2016,
            "gpa": 3.8,
        }
    ],
    "projects": [
        {
            "name": "OpenResume",
            "description": "Open-source resume parser with NLP extraction",
            "technologies": ["Python", "spaCy", "FastAPI"],
            "url": "https://github.com/alicejohnson/openresume",
        }
    ],
    "certifications": [
        {
            "name": "AWS Solutions Architect",
            "issuing_organization": "Amazon Web Services",
            "issue_date": "2022-03-01",
            "expiry_date": "2025-03-01",
            "credential_id": "AWS-SAA-C03-12345",
        }
    ],
}

SAMPLE_RESUME_TEXT = """
Alice Johnson
alice@example.com | +1-555-0100 | linkedin.com/in/alicejohnson | github.com/alicejohnson
San Francisco, CA

PROFESSIONAL SUMMARY
Senior software engineer with 7 years of backend experience in Python, microservices, and cloud infrastructure.

TECHNICAL SKILLS
Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, Node.js, MongoDB

EXPERIENCE

Senior Software Engineer - TechCorp Inc., San Francisco, CA | June 2020 - Present
- Led design of microservices architecture serving 5M users
- Reduced API latency by 40% through Redis caching
Technologies: Python, FastAPI, Redis, PostgreSQL

Software Engineer - StartupXYZ, Remote | January 2017 - May 2020
- Built RESTful APIs
- Implemented CI/CD pipelines
Technologies: Node.js, MongoDB, Jenkins

EDUCATION
UC Berkeley - Bachelor of Science in Computer Science, 2016, GPA: 3.8

PROJECTS
OpenResume - Open-source resume parser with NLP extraction
Technologies: Python, spaCy, FastAPI
URL: https://github.com/alicejohnson/openresume

CERTIFICATIONS
AWS Solutions Architect - Amazon Web Services - Issued March 2022 - Expires March 2025
Credential ID: AWS-SAA-C03-12345

LANGUAGES
English (Native), Spanish (Conversational)
"""

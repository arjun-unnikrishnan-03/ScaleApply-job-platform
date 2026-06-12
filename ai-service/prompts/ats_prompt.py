"""
ATSEvaluationPrompt — the prompt that drives the ATS Intelligence Agent.

Design decisions:
1. The prompt takes JSON dumps of both the CandidateProfile and the JobDescription.
2. We enforce strict JSON output that maps directly to the ATSResult schema.
3. System rules enforce objective comparison.
"""

from __future__ import annotations

import json

from prompts.base import PromptTemplate
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert ATS (Applicant Tracking System) AI for an enterprise recruitment platform.
Your task is to objectively evaluate a Candidate Profile against a Job Description.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Evaluate technical fit, experience fit, and project relevance.
3. Be brutally honest and objective. If a skill is missing, list it in missing_skills.
4. Calculate a match score from 0.0 to 100.0 based on how well the candidate meets the requirements.
5. Provide a clear, professional explanation for your score.
6. Identify specific strengths and weaknesses based ONLY on the provided profiles. Do NOT invent information.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "score": "float (0.0 to 100.0, required)",
  "matched_skills": ["string", "..."],
  "missing_skills": ["string", "..."],
  "strengths": ["string", "..."],
  "weaknesses": ["string", "..."],
  "recommendations": ["string", "..."],
  "explanation": "string (required)"
}
"""


class ATSEvaluationPrompt(PromptTemplate):
    """
    Builds the complete prompt for ATS evaluation.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Evaluates a CandidateProfile against a JobDescription and outputs an ATSResult JSON."

    def build(self, candidate: CandidateProfile, job: JobDescription, **kwargs) -> str:  # type: ignore[override]
        """
        Render the full evaluation prompt.

        Args:
            candidate: Validated CandidateProfile object.
            job: Validated JobDescription object.

        Returns:
            Complete prompt string ready for the LLM provider.
        """
        # Dump the Pydantic models to clean JSON, excluding None values
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Evaluate the candidate against the job description.
Return ONLY the JSON object. No explanation, no markdown.

--- CANDIDATE PROFILE START ---
{candidate_json}
--- CANDIDATE PROFILE END ---

--- JOB DESCRIPTION START ---
{job_json}
--- JOB DESCRIPTION END ---

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(self, candidate: CandidateProfile, job: JobDescription) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Evaluate the candidate against the job description:

--- CANDIDATE PROFILE START ---
{candidate_json}
--- CANDIDATE PROFILE END ---

--- JOB DESCRIPTION START ---
{job_json}
--- JOB DESCRIPTION END ---

JSON OUTPUT:"""

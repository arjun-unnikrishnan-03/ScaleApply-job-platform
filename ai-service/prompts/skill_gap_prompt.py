"""
SkillGapPrompt — the prompt that drives the Skill Gap Agent.

Design decisions:
1. Takes JSON dumps of CandidateProfile, JobDescription, and ATSResult.
2. Enforces strict JSON output mapping to the SkillGapResult schema.
3. System rules enforce prioritization and actionable advice.
"""

from __future__ import annotations

import json

from prompts.base import PromptTemplate
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert Technical Recruiter and Career Coach AI.
Your task is to analyze a candidate's skill gaps for a specific job based on their profile and ATS evaluation.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Calculate a match_percentage based on the overlapping required skills and ATS score (0.0 to 100.0).
3. Identify exactly which skills are missing.
4. Order the missing skills by priority_order (most critical for the job first).
5. Estimate the total weeks of learning effort (estimated_learning_weeks) required to bridge the gap.
6. Create an actionable roadmap with specific steps for the highest priority missing skills.
7. Provide a concise explanation of the overall gap and learning strategy.
8. Do NOT invent skills that are not mentioned in the Job Description.
9. Do NOT generate interview questions or recommend hiring decisions.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "match_percentage": "float (0.0 to 100.0, required)",
  "missing_skills": ["string", "..."],
  "priority_order": ["string (ordered most critical first)", "..."],
  "estimated_learning_weeks": "float (0.0 or greater, required)",
  "strengths": ["string", "..."],
  "roadmap": [
    {
      "skill_name": "string (required)",
      "actionable_advice": "string (required)",
      "estimated_weeks": "float (required)"
    }
  ],
  "explanation": "string (required)"
}
"""


class SkillGapPrompt(PromptTemplate):
    """
    Builds the complete prompt for skill gap analysis.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Evaluates Candidate, Job, and ATS data to generate a SkillGapResult JSON."

    def build(self, candidate: CandidateProfile, job: JobDescription, ats_result: ATSResult, **kwargs) -> str:  # type: ignore[override]
        """
        Render the full evaluation prompt.

        Args:
            candidate: Validated CandidateProfile object.
            job: Validated JobDescription object.
            ats_result: Validated ATSResult object.

        Returns:
            Complete prompt string ready for the LLM provider.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Analyze the skill gaps based on the provided profiles and ATS evaluation.
Return ONLY the JSON object. No explanation, no markdown.

--- CANDIDATE PROFILE START ---
{candidate_json}
--- CANDIDATE PROFILE END ---

--- JOB DESCRIPTION START ---
{job_json}
--- JOB DESCRIPTION END ---

--- ATS RESULT START ---
{ats_json}
--- ATS RESULT END ---

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(self, candidate: CandidateProfile, job: JobDescription, ats_result: ATSResult) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Analyze the skill gaps based on the provided profiles and ATS evaluation:

--- CANDIDATE PROFILE START ---
{candidate_json}
--- CANDIDATE PROFILE END ---

--- JOB DESCRIPTION START ---
{job_json}
--- JOB DESCRIPTION END ---

--- ATS RESULT START ---
{ats_json}
--- ATS RESULT END ---

JSON OUTPUT:"""

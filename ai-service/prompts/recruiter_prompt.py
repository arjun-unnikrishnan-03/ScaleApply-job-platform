"""
RecruiterPrompt — the prompt that drives the Recruiter Agent.

Design decisions:
1. Takes JSON dumps of all 5 domain models (Candidate, Job, ATS, SkillGap, Interview).
2. Enforces strict JSON output mapping to the RecruiterDecision schema.
3. Instructs the LLM to act as a senior hiring manager synthesizing multiple data sources.
"""

from __future__ import annotations

import json

from prompts.base import PromptTemplate
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult
from models.interview_result import InterviewResult


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert Senior Hiring Manager and Executive Recruiter AI.
Your task is to synthesize all available intelligence on a candidate to make a final hiring recommendation.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Evaluate the candidate holistically using the ATS score, skill gaps, and generated interview focus.
3. Set the 'recommendation' strictly to one of: "StrongHire", "Hire", "Consider", "Reject".
4. Set the 'confidence' strictly as a float between 0.0 and 1.0 representing your certainty.
5. Identify the top 'strengths' and critical 'risks'.
6. Provide specific 'interview_focus_areas' that the human interviewer must probe before a final offer.
7. Write a concise executive 'summary' (1-2 sentences).
8. Write detailed 'reasoning' justifying the recommendation and confidence score.
9. Do NOT invent data. Base all conclusions on the provided profiles and intelligence results.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "recommendation": "string ('StrongHire', 'Hire', 'Consider', 'Reject', required)",
  "confidence": "float (0.0 to 1.0, required)",
  "strengths": ["string", "..."],
  "risks": ["string", "..."],
  "interview_focus_areas": ["string", "..."],
  "summary": "string (required)",
  "reasoning": "string (required)"
}
"""


class RecruiterPrompt(PromptTemplate):
    """
    Builds the complete prompt for recruiter decision generation.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Generates a RecruiterDecision JSON synthesizing Candidate, Job, ATS, SkillGap, and Interview data."

    def build(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        ats_result: ATSResult,
        skill_gap_result: SkillGapResult,
        interview_result: InterviewResult,
        **kwargs
    ) -> str:  # type: ignore[override]
        """
        Render the full evaluation prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)
        skill_gap_json = skill_gap_result.model_dump_json(exclude_none=True, indent=2)
        interview_json = interview_result.model_dump_json(exclude_none=True, indent=2)

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Evaluate the candidate holistically and provide your recommendation.
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

--- SKILL GAP RESULT START ---
{skill_gap_json}
--- SKILL GAP RESULT END ---

--- INTERVIEW RESULT START ---
{interview_json}
--- INTERVIEW RESULT END ---

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        ats_result: ATSResult,
        skill_gap_result: SkillGapResult,
        interview_result: InterviewResult
    ) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)
        skill_gap_json = skill_gap_result.model_dump_json(exclude_none=True, indent=2)
        interview_json = interview_result.model_dump_json(exclude_none=True, indent=2)

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Evaluate the candidate holistically and provide your recommendation:

--- CANDIDATE PROFILE START ---
{candidate_json}
--- CANDIDATE PROFILE END ---

--- JOB DESCRIPTION START ---
{job_json}
--- JOB DESCRIPTION END ---

--- ATS RESULT START ---
{ats_json}
--- ATS RESULT END ---

--- SKILL GAP RESULT START ---
{skill_gap_json}
--- SKILL GAP RESULT END ---

--- INTERVIEW RESULT START ---
{interview_json}
--- INTERVIEW RESULT END ---

JSON OUTPUT:"""

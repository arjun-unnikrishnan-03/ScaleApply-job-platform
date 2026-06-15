"""
InterviewPrompt — the prompt that drives the Interview Agent.

Design decisions:
1. Takes JSON dumps of CandidateProfile, JobDescription, ATSResult, and SkillGapResult.
2. Enforces strict JSON output mapping to the InterviewResult schema.
3. Requires unique questions across four distinct categories.
"""

from __future__ import annotations

import json

from prompts.base import PromptTemplate
from models.candidate_profile import CandidateProfile
from models.job_description import JobDescription
from models.ats_result import ATSResult
from models.skill_gap_result import SkillGapResult


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert Technical Interviewer and Hiring Manager AI.
Your task is to generate highly personalized interview questions based on a candidate's profile, job requirements, ATS evaluation, and identified skill gaps.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. All questions MUST be highly tailored to the provided inputs. Avoid generic questions like "What are your strengths?" unless tied to a specific ATS finding.
3. Every question must have a 'difficulty' of 'Easy', 'Medium', or 'Hard'.
4. Generate Technical Questions based on the candidate's skills and the job's required technologies.
5. Generate Project Questions probing the specific projects mentioned in the candidate's profile.
6. Generate Behavioral Questions aligned with the job's responsibilities and the candidate's experience.
7. Generate Weak Area Questions specifically targeting the missing skills or weaknesses identified in the ATS Result and Skill Gap Result.
8. Every question MUST have a clear 'reason' explaining why it is being asked for this specific candidate and job.
9. Provide an 'evaluation_rubric' with clear criteria on what constitutes a passing score for the overall interview.
10. Provide an overall 'explanation' summarizing the interview strategy.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "technical_questions": [
    {
      "question": "string (required)",
      "category": "Technical",
      "difficulty": "string ('Easy', 'Medium', 'Hard')",
      "reason": "string (required)"
    }
  ],
  "project_questions": [
    {
      "question": "string (required)",
      "category": "Project",
      "difficulty": "string ('Easy', 'Medium', 'Hard')",
      "reason": "string (required)"
    }
  ],
  "behavioral_questions": [
    {
      "question": "string (required)",
      "category": "Behavioral",
      "difficulty": "string ('Easy', 'Medium', 'Hard')",
      "reason": "string (required)"
    }
  ],
  "weak_area_questions": [
    {
      "question": "string (required)",
      "category": "Weak Area",
      "difficulty": "string ('Easy', 'Medium', 'Hard')",
      "reason": "string (required)"
    }
  ],
  "evaluation_rubric": [
    {
      "criteria": "string (required)",
      "passing_score_description": "string (required)"
    }
  ],
  "explanation": "string (required)"
}
"""


class InterviewPrompt(PromptTemplate):
    """
    Builds the complete prompt for interview generation.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Generates a highly personalized InterviewResult JSON based on candidate, job, ATS, and skill gap data."

    def build(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        ats_result: ATSResult,
        skill_gap_result: SkillGapResult,
        **kwargs
    ) -> str:  # type: ignore[override]
        """
        Render the full evaluation prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)
        skill_gap_json = skill_gap_result.model_dump_json(exclude_none=True, indent=2)

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Generate personalized interview questions based on the following profiles and evaluations.
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
        skill_gap_result: SkillGapResult
    ) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        candidate_json = candidate.model_dump_json(exclude_none=True, indent=2)
        job_json = job.model_dump_json(exclude_none=True, indent=2)
        ats_json = ats_result.model_dump_json(exclude_none=True, indent=2)
        skill_gap_json = skill_gap_result.model_dump_json(exclude_none=True, indent=2)

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Generate personalized interview questions based on the following profiles and evaluations:

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

JSON OUTPUT:"""

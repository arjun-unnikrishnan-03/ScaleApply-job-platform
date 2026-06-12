"""
JobExtractionPrompt — the prompt that drives the Job Intelligence Agent.

Design decisions:
1. The JSON schema is curated to be LLM-friendly, mirroring JobDescription.
2. The prompt is structured as a system+user composite to work with both
   chat-style APIs and completion APIs.
3. Strong negative constraints ("do not invent", "use null") reduce hallucinations.
4. Explicit instructions on normalizing skills, extracting technologies, and
   extracting years of experience.
"""

from __future__ import annotations

from prompts.base import PromptTemplate


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert HR and recruitment AI for an enterprise recruitment platform.
Your task is to extract structured information from unstructured job descriptions with high precision.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Do NOT invent or hallucinate information. If data is absent, use null or [].
3. Extract EXACTLY what is required by the schema. Do not paraphrase or embellish, unless normalizing terms.
4. Normalize employment types (e.g., "Full Time" -> "full_time", "Contract" -> "contract").
5. Extract all required skills as individual items (e.g., ["Python", "AWS", "Communication"]).
6. Identify specific technologies and tools and list them under 'technologies'.
7. Extract the minimum and maximum years of experience required. If only a minimum is provided (e.g., "5+ years"), set max_years to null.
8. Extract the experience level (entry, mid, senior, lead, principal, director) based on the title and description.
9. If the document is not a job description, return: {"title": "UNKNOWN", "error": "Not a job description"}.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "title": "string (required)",
  "department": "string or null",
  "company_name": "string or null",
  "location": "string or null",
  "remote_policy": "string or null ('remote', 'hybrid', 'on-site')",
  "employment_type": "string ('full_time', 'part_time', 'contract', 'internship', 'freelance', 'temporary', 'unknown')",
  "experience_required": {
    "min_years": "float (required)",
    "max_years": "float or null",
    "level": "string ('entry', 'mid', 'senior', 'lead', 'principal', 'director', 'unknown')",
    "raw_text": "string or null (e.g., '5+ years of experience')"
  } or null,
  "required_skills": ["string", "..."],
  "preferred_skills": ["string", "..."],
  "technologies": ["string", "..."],
  "responsibilities": ["string", "..."],
  "qualifications": ["string", "..."],
  "benefits": [
    {
      "name": "string (required)",
      "description": "string or null"
    }
  ],
  "salary_range": {
    "min_amount": "float or null",
    "max_amount": "float or null",
    "currency": "string (e.g., 'USD')",
    "period": "string ('annual', 'monthly', 'hourly')",
    "raw_text": "string or null"
  } or null,
  "summary": "string or null"
}
"""


class JobExtractionPrompt(PromptTemplate):
    """
    Builds the complete prompt for job description structured extraction.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Extracts a structured JobDescription JSON from raw job posting text."

    def build(self, job_text: str, **kwargs) -> str:  # type: ignore[override]
        """
        Render the full extraction prompt.

        Args:
            job_text: Raw text extracted from the job description.

        Returns:
            Complete prompt string ready for the LLM provider.
        """
        if not job_text or not job_text.strip():
            raise ValueError("job_text cannot be empty.")

        max_chars = 12_000
        if len(job_text) > max_chars:
            job_text = job_text[:max_chars] + "\n[TRUNCATED]"

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Now extract structured data from the following job description text.
Return ONLY the JSON object. No explanation, no markdown.

--- JOB DESCRIPTION START ---
{job_text}
--- JOB DESCRIPTION END ---

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(self, job_text: str) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        max_chars = 12_000
        if len(job_text) > max_chars:
            job_text = job_text[:max_chars] + "\n[TRUNCATED]"

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Extract from this job description:

--- JOB DESCRIPTION START ---
{job_text}
--- JOB DESCRIPTION END ---

JSON OUTPUT:"""

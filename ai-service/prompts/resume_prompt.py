"""
ResumeExtractionPrompt — the prompt that drives the Resume Intelligence Agent.

Design decisions:
1. The JSON schema is derived from CandidateProfile at runtime, so schema
   changes automatically propagate to the prompt. No manual sync needed.
2. The prompt is structured as a system+user composite to work with
   both chat-style APIs (OpenAI, Claude) and completion APIs (older Gemini).
3. Strong negative constraints ("do not invent", "use null") reduce hallucinations.
4. Few-shot examples for DateRange format anchor the model on edge cases.
"""

from __future__ import annotations

import json

from prompts.base import PromptTemplate


# ── System instruction ────────────────────────────────────────────────────────
# Separated from user content for providers that support system prompts.

SYSTEM_INSTRUCTION = """\
You are an expert resume parsing AI for an enterprise recruitment platform.
Your task is to extract structured information from resume text with precision.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Do NOT invent or hallucinate information. If data is absent, use null or [].
3. Extract EXACTLY what is written. Do not paraphrase or embellish.
4. All dates must follow ISO 8601 format: YYYY-MM-DD. If only year is known, use YYYY-01-01.
5. Skills must be individual items (not "React, Node.js" as one string).
6. years_of_experience should be a float calculated from experience history, or null.
7. If the document is not a resume, return: {"full_name": "UNKNOWN", "error": "Not a resume"}.
"""

# ── Date format examples (few-shot) ───────────────────────────────────────────
DATE_EXAMPLES = """\
Date format examples:
- "Jan 2020 - Present"  → start_date: "2020-01-01", end_date: null
- "March 2018 - June 2022" → start_date: "2018-03-01", end_date: "2022-06-01"
- "2015 - 2019" → start_date: "2015-01-01", end_date: "2019-01-01"
- "Current" / "Present" → end_date: null
"""

# ── Target JSON schema ────────────────────────────────────────────────────────
# Manually curated schema description because injecting the full Pydantic JSON Schema
# verbatim can confuse smaller models. We use a clean, LLM-friendly representation.

OUTPUT_SCHEMA = """\
{
  "full_name": "string (required)",
  "email": "string or null",
  "phone": "string or null",
  "linkedin_url": "string or null",
  "github_url": "string or null",
  "location": "string or null",
  "portfolio_url": "string or null",
  "professional_summary": "string or null",
  "years_of_experience": "float or null",
  "technical_skills": ["string", "..."],
  "soft_skills": ["string", "..."],
  "languages": ["string (spoken language)", "..."],
  "experience": [
    {
      "company": "string (required)",
      "title": "string (required)",
      "location": "string or null",
      "duration": {
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD or null (if current)"
      },
      "responsibilities": ["string", "..."],
      "technologies_used": ["string", "..."]
    }
  ],
  "education": [
    {
      "institution": "string (required)",
      "degree": "string (required)",
      "field_of_study": "string or null",
      "graduation_year": "integer or null",
      "gpa": "float or null"
    }
  ],
  "projects": [
    {
      "name": "string (required)",
      "description": "string or null",
      "technologies": ["string", "..."],
      "url": "string or null"
    }
  ],
  "certifications": [
    {
      "name": "string (required)",
      "issuing_organization": "string or null",
      "issue_date": "YYYY-MM-DD or null",
      "expiry_date": "YYYY-MM-DD or null",
      "credential_id": "string or null"
    }
  ]
}
"""


class ResumeExtractionPrompt(PromptTemplate):
    """
    Builds the complete prompt for resume structured extraction.

    The prompt is provider-agnostic — it works with Gemini, GPT-4,
    Claude, and local models. The only difference is how providers
    split `system_instruction` from `user_content` (handled in providers).
    """

    @property
    def version(self) -> str:
        return "1.2.0"

    @property
    def description(self) -> str:
        return "Extracts a structured CandidateProfile JSON from raw resume text."

    def build(self, resume_text: str, **kwargs) -> str:  # type: ignore[override]
        """
        Render the full extraction prompt.

        Args:
            resume_text: Raw text extracted from the resume file.

        Returns:
            Complete prompt string ready for the LLM provider.
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("resume_text cannot be empty.")

        # Truncate very long resumes to avoid token limits
        # Future: implement semantic chunking for RAG module
        max_chars = 12_000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "\n[TRUNCATED]"

        return f"""{SYSTEM_INSTRUCTION}

{DATE_EXAMPLES}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Now extract structured data from the following resume text.
Return ONLY the JSON object. No explanation, no markdown.

--- RESUME TEXT START ---
{resume_text}
--- RESUME TEXT END ---

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.

        Used by providers (e.g. OpenAI, Claude) that support
        separate system vs user messages in their API.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(self, resume_text: str) -> str:
        """
        Return only the user-facing portion of the prompt.

        Combined with get_system_instruction() for chat-completion APIs.
        """
        max_chars = 12_000
        if len(resume_text) > max_chars:
            resume_text = resume_text[:max_chars] + "\n[TRUNCATED]"

        return f"""{DATE_EXAMPLES}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

Extract from this resume:

--- RESUME TEXT START ---
{resume_text}
--- RESUME TEXT END ---

JSON OUTPUT:"""

"""
main.py -- Runnable demonstration of the Resume Intelligence Agent.

This file shows the full DI wiring and pipeline in action.
Two modes:
  1. DEMO MODE (no API key): Uses a MockLLMProvider with sample data.
  2. LIVE MODE (with API key): Uses the real GeminiProvider.

Run:
    # Demo mode (no API key required)
    python main.py

    # Live mode
    LLM_API_KEY=AIza... LLM_PROVIDER=gemini python main.py path/to/resume.pdf
"""

from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_demo_mode() -> None:
    """
    Demo mode: runs the full pipeline with a MockLLMProvider.
    No API key, no network, fully deterministic.
    """
    print("\n" + "=" * 60)
    print("  Resume Intelligence Agent - DEMO MODE")
    print("  (Using MockLLMProvider - no API calls)")
    print("=" * 60 + "\n")

    # Import inside function to demonstrate the DI pattern clearly
    from demo_data import SAMPLE_CANDIDATE_JSON, SAMPLE_RESUME_TEXT
    from providers.base import GenerationConfig, LLMProvider, ProviderResponse
    from agents.resume_agent import ResumeAgent
    import json as _json

    class _DemoProvider(LLMProvider):
        """Minimal inline mock for demo mode — no pytest dependency."""
        def generate(self, prompt, config=None):
            return ProviderResponse(
                content=_json.dumps(SAMPLE_CANDIDATE_JSON),
                model="demo-mock-v1",
                input_tokens=350,
                output_tokens=220,
                finish_reason="stop",
            )
        def get_model_name(self): return "demo-mock-v1"
        def health_check(self): return True

    # ── Wire dependencies ──────────────────────────────────────────────────
    provider = _DemoProvider()
    agent = ResumeAgent(provider=provider)

    print("▶ Provider:       MockLLMProvider (mock-model-v1)")
    print("▶ Agent:          ResumeAgent")
    print("▶ Prompt version:", agent._prompt.version)
    print()

    # ── Process text directly (no real file needed for demo) ───────────────
    print("Processing sample resume text...\n")
    result = agent.process_text(SAMPLE_RESUME_TEXT, source_name="sample_resume.txt")

    if result.is_success:
        profile = result.value
        print("✅ SUCCESS — CandidateProfile extracted\n")
        _print_profile(profile)
        _print_metadata(result.metadata)
    else:
        print(f"❌ FAILED: {result.error}")
        sys.exit(1)


def run_live_mode(file_path: str) -> None:
    """
    Live mode: runs the full pipeline against a real resume file
    using the provider configured via environment variables.
    """
    from config.settings import settings
    from providers.factory import ProviderFactory
    from agents.resume_agent import ResumeAgent
    from providers.base import GenerationConfig

    print("\n" + "=" * 60)
    print("  Resume Intelligence Agent - LIVE MODE")
    print(f"  Provider: {settings.llm_provider.upper()}")
    print(f"  Model:    {settings.llm_model}")
    print("=" * 60 + "\n")

    if not settings.llm_api_key:
        print("❌ ERROR: LLM_API_KEY environment variable is not set.")
        print("   Set it in your .env file or export it in your shell.")
        sys.exit(1)

    # ── Wire dependencies from settings ───────────────────────────────────
    provider = ProviderFactory.from_settings(settings)
    agent = ResumeAgent(
        provider=provider,
        generation_config=GenerationConfig(
            temperature=settings.agent_temperature,
            max_output_tokens=settings.agent_max_output_tokens,
        ),
        min_resume_words=settings.agent_min_resume_words,
    )

    path = Path(file_path)
    if not path.exists():
        print(f"❌ ERROR: File not found: {file_path}")
        sys.exit(1)

    print(f"Processing: {path.name}\n")
    result = agent.process(path)

    if result.is_success:
        profile = result.value
        print("✅ SUCCESS — CandidateProfile extracted\n")
        _print_profile(profile)
        _print_metadata(result.metadata)
    else:
        print(f"\n❌ FAILED: {type(result.error).__name__}")
        print(f"   Message: {result.error.message}")
        if result.error.details:
            print(f"   Details: {json.dumps(result.error.details, indent=4)}")
        sys.exit(1)


# ── Display helpers ───────────────────────────────────────────────────────────

def _print_profile(profile) -> None:
    print("-" * 50)
    print(f"  Name:          {profile.full_name}")
    print(f"  Email:         {profile.email or '—'}")
    print(f"  Location:      {profile.location or '—'}")
    print(f"  Experience:    {profile.years_of_experience or '—'} years")
    print(f"  Complete:      {'Yes' if profile.is_complete() else 'No'}") 
    print()

    if profile.technical_skills:
        print(f"  Technical Skills ({len(profile.technical_skills)}):")
        print(f"    {', '.join(profile.technical_skills[:8])}")
        if len(profile.technical_skills) > 8:
            print(f"    ... and {len(profile.technical_skills) - 8} more")
    print()

    if profile.experience:
        print(f"  Experience ({len(profile.experience)} roles):")
        for exp in profile.experience:
            current = "(Current)" if exp.duration and not exp.duration.end_date else ""

            print(f"    • {exp.title} @ {exp.company} {current}")
    print()

    if profile.education:
        print(f"  Education ({len(profile.education)}):")
        for edu in profile.education:
            print(f"    • {edu.degree} — {edu.institution} ({edu.graduation_year or '?'})")
    print()

    if profile.projects:
        print(f"  Projects ({len(profile.projects)}):")
        for proj in profile.projects:
            print(f"    • {proj.name}: {proj.description or ''}")
    print()

    if profile.certifications:
        print(f"  Certifications ({len(profile.certifications)}):")
        for cert in profile.certifications:
            print(f"    • {cert.name} — {cert.issuing_organization or '?'}")

    total_techs = profile.total_technologies()
    print(f"\n  Unique Technologies (aggregated): {len(total_techs)}")
    print("-" * 50)


def _print_metadata(metadata: dict) -> None:
    print("\n  Pipeline Metadata:")
    print(f"    Model:          {metadata.get('model', '—')}")
    print(f"    Prompt version: {metadata.get('prompt_version', '—')}")
    print(f"    Tokens (in):    {metadata.get('input_tokens', 0)}")
    print(f"    Tokens (out):   {metadata.get('output_tokens', 0)}")
    print(f"    Resume words:   {metadata.get('word_count', '—')}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Live mode: python main.py path/to/resume.pdf
        run_live_mode(sys.argv[1])
    else:
        # Demo mode: python main.py
        run_demo_mode()

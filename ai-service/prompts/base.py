"""
Prompt module base class.

Prompts are first-class citizens in this architecture — they are
versioned, testable, and completely decoupled from any LLM SDK.

A PromptTemplate:
1. Knows the domain schema it targets (CandidateProfile)
2. Accepts raw text (from parsers) as input
3. Produces a complete, ready-to-send prompt string
4. Documents its own system context and output expectations
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PromptTemplate(ABC):
    """
    Abstract base class for all agent prompt templates.

    Each agent (Resume, ATS, Interview, etc.) owns its own
    PromptTemplate subclass. This allows prompt engineering to
    be iterated independently from agent logic.
    """

    @abstractmethod
    def build(self, **kwargs) -> str:
        """
        Render the prompt with the given context variables.

        Returns:
            A fully rendered prompt string ready to be sent to an LLM.
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of this prompt (e.g. '1.0.0')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable summary of what this prompt extracts."""

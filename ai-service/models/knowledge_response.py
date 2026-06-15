"""
KnowledgeResponse — domain model representing the final answer from the KnowledgeAgent.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

NonEmptyStr = Annotated[str, Field(min_length=1)]
ConfidenceFloat = Annotated[float, Field(ge=0.0, le=1.0)]

class KnowledgeResponse(BaseModel):
    """
    The final answer provided by the KnowledgeAgent, including the synthesized
    answer, strict confidence bounds, and unique sources.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    answer: NonEmptyStr
    sources: list[str] = Field(default_factory=list)
    confidence: ConfidenceFloat

    @field_validator("sources", mode="before")
    @classmethod
    def deduplicate_sources(cls, items: object) -> list[str]:
        """Strip and deduplicate source paths/names."""
        if not isinstance(items, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            clean = item.strip()
            lower = clean.lower()
            if clean and lower not in seen:
                seen.add(lower)
                result.append(clean)
        return result

"""
KnowledgeDocument — the domain model for knowledge base records.

This model is strictly validated to ensure documents moving into the
vector store have consistent metadata and unique tags.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1)]


class KnowledgeDocument(BaseModel):
    """
    The domain object representing a static knowledge asset.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: NonEmptyStr
    category: NonEmptyStr
    content: NonEmptyStr
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def deduplicate_tags(cls, items: object) -> list[str]:
        """Strip and deduplicate tags while preserving case."""
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

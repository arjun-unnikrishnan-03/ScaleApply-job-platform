"""
KnowledgeChunk - the domain model representing a chunk of a larger knowledge document.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ──────────────────────────────────────────────
# Reusable annotation types
# ──────────────────────────────────────────────

NonEmptyStr = Annotated[str, Field(min_length=1)]


class KnowledgeChunk(BaseModel):
    """
    A semantic chunk of a larger KnowledgeDocument, used for precise vector retrieval.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: NonEmptyStr
    title: NonEmptyStr
    category: NonEmptyStr
    chunk_index: int = Field(ge=0)
    content: NonEmptyStr
    tags: list[str] = Field(default_factory=list)

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

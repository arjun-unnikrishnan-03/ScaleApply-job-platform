"""
EmbeddingResult — the domain model mapping a document to its vector representation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class EmbeddingResult(BaseModel):
    """
    Represents the output from an EmbeddingProvider, linking a document ID
    to its computed vector representation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    vector: list[float] = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

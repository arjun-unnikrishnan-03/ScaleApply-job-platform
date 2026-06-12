"""
RetrievalMetrics - the domain model for representing retrieval evaluation results.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RetrievalMetrics(BaseModel):
    """
    Evaluation metrics for a single retrieval test case.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    top_1_hit: bool
    top_3_hit: bool
    top_5_hit: bool
    latency_ms: float = Field(ge=0.0)
    retrieved_documents: int = Field(ge=0)

"""
IndexingReport — domain model for the results of an indexing run.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class IndexingReport(BaseModel):
    """
    Summary report of a knowledge indexing operation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_documents: int = Field(ge=0)
    indexed_documents: int = Field(ge=0)
    failed_documents: int = Field(ge=0)
    duration_ms: float = Field(ge=0.0)

    @property
    def success_rate(self) -> float:
        """Calculate the percentage of successfully indexed documents."""
        if self.total_documents == 0:
            return 100.0
        return (self.indexed_documents / self.total_documents) * 100.0

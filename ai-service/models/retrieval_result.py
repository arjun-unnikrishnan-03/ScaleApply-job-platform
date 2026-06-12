"""
RetrievalResult — domain model representing the output of a vector store search.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from models.knowledge_document import KnowledgeDocument

class RetrievalResult(BaseModel):
    """
    Represents the output of the RetrievalService.
    Contains the user's query and the relevant documents retrieved.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    documents: list[KnowledgeDocument]
    scores: list[float]

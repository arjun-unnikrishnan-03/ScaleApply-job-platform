"""
Agent dependency injection — wires providers into agents.
All dependencies are resolved through FastAPI's Depends mechanism.
Routers never instantiate agents directly.
"""
from __future__ import annotations

from fastapi import Depends

from agents.resume_agent import ResumeAgent
from agents.job_agent import JobAgent
from agents.ats_agent import ATSAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.interview_agent import InterviewAgent
from agents.recruiter_agent import RecruiterAgent
from agents.knowledge_agent import KnowledgeAgent
from providers.base import LLMProvider
from embeddings.base import EmbeddingProvider
from vectorstores.base import VectorStore
from services.retrieval_service import RetrievalService
from services.embedding_service import EmbeddingService

from api.dependencies.providers import get_llm_provider
from api.dependencies.vectorstores import get_embedding_provider, get_vector_store


def get_resume_agent(provider: LLMProvider = Depends(get_llm_provider)) -> ResumeAgent:
    return ResumeAgent(provider=provider)


def get_job_agent(provider: LLMProvider = Depends(get_llm_provider)) -> JobAgent:
    return JobAgent(provider=provider)


def get_ats_agent(provider: LLMProvider = Depends(get_llm_provider)) -> ATSAgent:
    return ATSAgent(provider=provider)


def get_skill_gap_agent(provider: LLMProvider = Depends(get_llm_provider)) -> SkillGapAgent:
    return SkillGapAgent(provider=provider)


def get_interview_agent(provider: LLMProvider = Depends(get_llm_provider)) -> InterviewAgent:
    return InterviewAgent(provider=provider)


def get_recruiter_agent(provider: LLMProvider = Depends(get_llm_provider)) -> RecruiterAgent:
    return RecruiterAgent(provider=provider)


def get_retrieval_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    vector_store: VectorStore = Depends(get_vector_store),
) -> RetrievalService:
    return RetrievalService(provider=embedding_provider, vector_store=vector_store)


def get_embedding_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    vector_store: VectorStore = Depends(get_vector_store),
) -> EmbeddingService:
    return EmbeddingService(provider=embedding_provider, vector_store=vector_store)


def get_knowledge_agent(
    provider: LLMProvider = Depends(get_llm_provider),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> KnowledgeAgent:
    return KnowledgeAgent(provider=provider, retrieval_service=retrieval_service)

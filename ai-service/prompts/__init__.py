# prompts/__init__.py
from prompts.base import PromptTemplate
from prompts.resume_prompt import ResumeExtractionPrompt
from prompts.job_prompt import JobExtractionPrompt
from prompts.ats_prompt import ATSEvaluationPrompt
from prompts.skill_gap_prompt import SkillGapPrompt
from prompts.interview_prompt import InterviewPrompt
from prompts.recruiter_prompt import RecruiterPrompt
from prompts.knowledge_prompt import KnowledgePrompt

__all__ = ["PromptTemplate", "ResumeExtractionPrompt", "JobExtractionPrompt", "ATSEvaluationPrompt", "SkillGapPrompt", "InterviewPrompt", "RecruiterPrompt", "KnowledgePrompt"]

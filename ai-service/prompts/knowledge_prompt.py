"""
KnowledgePrompt — the prompt that drives the Knowledge Agent.

Takes the user's question and the retrieved documents, instructing
the LLM to formulate an answer strictly based on the provided context.
"""

from __future__ import annotations

from prompts.base import PromptTemplate
from models.retrieval_result import RetrievalResult


# ── System instruction ────────────────────────────────────────────────────────

SYSTEM_INSTRUCTION = """\
You are an expert technical knowledge assistant.
Your task is to answer the user's question using ONLY the provided context documents.

CRITICAL RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no commentary.
2. Formulate your 'answer' using information extracted from the provided 'CONTEXT DOCUMENTS'.
3. If the answer cannot be found in the context, your 'answer' MUST state that the information is unavailable, and your 'confidence' MUST be 0.0.
4. DO NOT hallucinate. Do not use outside knowledge.
5. In 'sources', list the unique 'source' identifiers of the documents you used to formulate the answer.
6. Provide a 'confidence' score between 0.0 and 1.0 representing how fully the context answers the question.
"""

# ── Target JSON schema ────────────────────────────────────────────────────────

OUTPUT_SCHEMA = """\
{
  "answer": "string (required)",
  "sources": ["string", "..."],
  "confidence": "float (0.0 to 1.0, required)"
}
"""


class KnowledgePrompt(PromptTemplate):
    """
    Builds the prompt for RAG-based knowledge synthesis.
    """

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Generates a KnowledgeResponse using retrieved context documents."

    def build(self, retrieval_result: RetrievalResult, **kwargs) -> str:  # type: ignore[override]
        """
        Render the full RAG prompt.
        """
        context_blocks = []
        for doc in retrieval_result.documents:
            context_blocks.append(
                f"--- DOCUMENT SOURCE: {doc.source} ---\n"
                f"TITLE: {doc.title}\n"
                f"CATEGORY: {doc.category}\n"
                f"CONTENT:\n{doc.content}\n"
                "---------------------------------------\n"
            )
        
        context_str = "\n".join(context_blocks) if context_blocks else "NO CONTEXT DOCUMENTS PROVIDED."

        return f"""{SYSTEM_INSTRUCTION}

TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

USER QUESTION:
{retrieval_result.query}

CONTEXT DOCUMENTS:
{context_str}

Analyze the CONTEXT DOCUMENTS to answer the USER QUESTION.
Return ONLY the JSON object.

JSON OUTPUT:"""

    def get_system_instruction(self) -> str:
        """
        Return just the system instruction portion.
        """
        return SYSTEM_INSTRUCTION

    def build_user_content(self, retrieval_result: RetrievalResult) -> str:
        """
        Return only the user-facing portion of the prompt.
        """
        context_blocks = []
        for doc in retrieval_result.documents:
            context_blocks.append(
                f"--- DOCUMENT SOURCE: {doc.source} ---\n"
                f"TITLE: {doc.title}\n"
                f"CATEGORY: {doc.category}\n"
                f"CONTENT:\n{doc.content}\n"
                "---------------------------------------\n"
            )
        
        context_str = "\n".join(context_blocks) if context_blocks else "NO CONTEXT DOCUMENTS PROVIDED."

        return f"""TARGET JSON SCHEMA:
{OUTPUT_SCHEMA}

USER QUESTION:
{retrieval_result.query}

CONTEXT DOCUMENTS:
{context_str}

Analyze the CONTEXT DOCUMENTS to answer the USER QUESTION.
Return ONLY the JSON object.

JSON OUTPUT:"""

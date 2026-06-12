from __future__ import annotations

import logging
from typing import Any, Dict

from api.dependencies.providers import get_llm_provider
from api.dependencies.vectorstores import get_embedding_provider, get_vector_store
from api.dependencies.agents import get_retrieval_service, get_knowledge_agent
from agents.knowledge_agent import KnowledgeAgent
from services.queue_service import QueueService
from workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class KnowledgeWorker(BaseWorker):
    """
    Worker for processing RAG queries against the knowledge base asynchronously.
    Consumes from the 'knowledge.processing' stream.
    """

    def __init__(
        self,
        queue_service: QueueService,
        group: str = "workers-group",
        consumer_name: str | None = None,
    ) -> None:
        super().__init__(
            queue_service=queue_service,
            stream="knowledge.processing",
            group=group,
            consumer_name=consumer_name,
        )
        provider = get_llm_provider()
        emb_provider = get_embedding_provider()
        v_store = get_vector_store()
        ret_service = get_retrieval_service(emb_provider, v_store)
        self.agent = KnowledgeAgent(provider=provider, retrieval_service=ret_service)

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        """
        Executes KnowledgeAgent query.
        """
        query = payload.get("query")
        if not query:
            raise ValueError("Payload missing required 'query' field.")

        logger.info("Executing KnowledgeAgent ask...")
        result = self.agent.ask(query)

        if not result.is_success:
            logger.error("KnowledgeAgent query failed: %s", result.error)
            raise result.error

        response = result.unwrap()
        return {
            "query": query,
            "documents": [{"content": response.answer, "sources": response.sources}],
            "scores": [response.confidence],
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    qs = QueueService()
    worker = KnowledgeWorker(qs)
    worker.start()

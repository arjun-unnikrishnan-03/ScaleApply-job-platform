"""
FastAPI Application Factory.

Builds and configures the production-ready AI microservice with:
- Middleware (request ID, structured logging)
- Global exception handlers
- All domain routers
- OpenAPI metadata
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from pydantic import ValidationError as PydanticValidationError

from api.middleware.error_handler import (
    pydantic_validation_handler,
    recruitment_error_handler,
    unhandled_exception_handler,
)
from api.middleware.logging import LoggingMiddleware
from api.middleware.request_id import RequestIDMiddleware
from api.routers import ats, health, interview, job, knowledge, recruiter, resume, skill_gap
from config.settings import settings
from core.exceptions import RecruitmentError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Application factory — creates and fully configures the FastAPI instance.

    Using a factory pattern allows easy test instantiation with overrides.
    """
    app = FastAPI(
        title="ScaleApply AI Platform",
        description=(
            "Production-ready AI microservice providing resume intelligence, "
            "ATS analysis, skill gap identification, interview preparation, "
            "recruiter evaluation, and RAG-powered knowledge queries."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "ScaleApply Engineering",
        },
        license_info={
            "name": "Proprietary",
        },
    )

    # ── Middleware (applied LIFO — last added = outermost) ────────────────────
    # LoggingMiddleware wraps innermost so it sees request_id from RequestIDMiddleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(RecruitmentError, recruitment_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(resume.router)
    app.include_router(job.router)
    app.include_router(ats.router)
    app.include_router(skill_gap.router)
    app.include_router(interview.router)
    app.include_router(recruiter.router)
    app.include_router(knowledge.router)
    @app.on_event("startup")
    def on_startup() -> None:
        print(">>> FastAPI on_startup event handler triggered! <<<", flush=True)
        from api.dependencies.vectorstores import get_vector_store, get_embedding_provider
        from api.dependencies.agents import get_embedding_service
        from indexers.knowledge_indexer import KnowledgeIndexer
        from loaders.knowledge_loader import KnowledgeLoader
        from pathlib import Path

        try:
            vector_store = get_vector_store()
            is_mem = getattr(vector_store, "is_memory_store", False)
            print(f">>> Resolved vector store: {vector_store}, is_memory_store={is_mem} <<<", flush=True)
            if is_mem:
                print(">>> Starting startup indexing of local knowledge... <<<", flush=True)
                logger.info("Vector store is using in-memory fallback. Starting startup indexing of local knowledge...")
                knowledge_dir = Path(__file__).parent.parent / "knowledge"
                loader = KnowledgeLoader(knowledge_dir)
                embedding_service = get_embedding_service(
                    embedding_provider=get_embedding_provider(),
                    vector_store=vector_store
                )
                
                # Run indexer WITHOUT chunking so that KnowledgeAgent.ask() works properly with complete documents
                indexer = KnowledgeIndexer(loader, embedding_service)
                result = indexer.index_all()
                if result.is_success:
                    report = result.unwrap()
                    print(f">>> Startup indexing completed successfully. Total: {report.total_documents}, Indexed: {report.indexed_documents}, Failed: {report.failed_documents} <<<", flush=True)
                    logger.info(
                        "Startup indexing completed successfully. Total docs: %d, Indexed: %d, Failed: %d",
                        report.total_documents,
                        report.indexed_documents,
                        report.failed_documents,
                    )
                else:
                    print(f">>> Startup indexing pipeline failed: {result.error} <<<", flush=True)
                    logger.error("Startup indexing pipeline failed: %s", result.error)
            else:
                logger.info("Vector store is not in-memory (persistent database is active). Skipping automatic indexing.")
        except Exception as exc:
            logger.exception("Failed during on-startup checks and indexing: %s", exc)

    logger.info("ScaleApply AI Platform started | log_level=%s", settings.log_level)
    return app


# Module-level app instance for uvicorn / ASGI servers
app = create_app()

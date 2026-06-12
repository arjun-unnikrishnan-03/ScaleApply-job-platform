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

    logger.info("ScaleApply AI Platform started | log_level=%s", settings.log_level)
    return app


# Module-level app instance for uvicorn / ASGI servers
app = create_app()

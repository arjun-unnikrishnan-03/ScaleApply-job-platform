"""
Health router — liveness and readiness probes.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.schemas.responses import HealthResponse
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns 200 if the service process is running.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get(
    "/ready",
    summary="Readiness check",
    description=(
        "Checks that all required external dependencies (Gemini API, Qdrant) "
        "are reachable. Returns 200 when ready, 503 when degraded."
    ),
)
async def ready() -> JSONResponse:
    checks: dict[str, str] = {}
    overall_ready = True

    # ── Gemini API key check (lightweight; no real call) ──────────────────────
    gemini_key = settings.gemini_api_key or settings.llm_api_key
    if gemini_key:
        checks["gemini"] = "configured"
    else:
        checks["gemini"] = "missing_api_key"
        overall_ready = False

    # ── Qdrant connectivity check ─────────────────────────────────────────────
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=3)
        client.get_collections()
        checks["qdrant"] = "connected"
    except Exception as exc:
        logger.warning("Readiness: Qdrant not reachable: %s", exc)
        checks["qdrant"] = "unreachable"
        overall_ready = False

    # ── Redis connectivity check ──────────────────────────────────────────────
    try:
        from services.queue_service import QueueService
        qs = QueueService()
        if qs.ping():
            checks["redis"] = "connected"
        else:
            checks["redis"] = "unreachable"
            overall_ready = False
    except Exception as exc:
        logger.warning("Readiness: Redis not reachable: %s", exc)
        checks["redis"] = "unreachable"
        overall_ready = False

    status_code = 200 if overall_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if overall_ready else "degraded", "checks": checks},
    )

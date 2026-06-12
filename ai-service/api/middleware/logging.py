"""
Structured Logging Middleware — logs timing, method, path, and status.
Intentionally NEVER logs request bodies, API keys, or embeddings.
"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured access log middleware.

    Logs:
        - request_id
        - method
        - path
        - status_code
        - duration_ms

    Never logs:
        - request body (may contain resume text)
        - Authorization / API keys
        - Embedding vectors
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s method=%s path=%s status=%d duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

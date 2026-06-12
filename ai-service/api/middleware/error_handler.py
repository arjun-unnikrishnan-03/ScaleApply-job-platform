"""
Global Exception Handler — maps domain exceptions to HTTP responses.

Mapping:
    GeminiProviderError / EmbeddingProviderError → 503 Service Unavailable
    QdrantConnectionError / QdrantSearchError    → 503 Service Unavailable
    ProviderRateLimitError                       → 429 Too Many Requests
    ValidationError (domain)                     → 422 Unprocessable Entity
    ExtractionError                              → 422 Unprocessable Entity
    RecruitmentError (any other)                 → 500 Internal Server Error
    Unhandled Exception                          → 500 Internal Server Error
"""
from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from core.exceptions import (
    EmbeddingProviderError,
    ExtractionError,
    GeminiProviderError,
    ProviderRateLimitError,
    QdrantConnectionError,
    QdrantSearchError,
    RecruitmentError,
    ValidationError as DomainValidationError,
)

logger = logging.getLogger("api.errors")


def _error_body(message: str, detail: str | dict | None = None) -> dict:
    return {"error": message, "detail": detail}


async def recruitment_error_handler(request: Request, exc: RecruitmentError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")

    if isinstance(exc, (GeminiProviderError, EmbeddingProviderError)):
        logger.error("request_id=%s AI provider error: %s", request_id, exc.message)
        return JSONResponse(
            status_code=503,
            content=_error_body("AI provider unavailable. Please try again later."),
        )

    if isinstance(exc, (QdrantConnectionError, QdrantSearchError)):
        logger.error("request_id=%s Vector store error: %s", request_id, exc.message)
        return JSONResponse(
            status_code=503,
            content=_error_body("Vector store unavailable. Please try again later."),
        )

    if isinstance(exc, ProviderRateLimitError):
        logger.warning("request_id=%s Rate limit hit: %s", request_id, exc.message)
        return JSONResponse(
            status_code=429,
            content=_error_body("Rate limit exceeded. Please retry after a moment."),
        )

    if isinstance(exc, (DomainValidationError, ExtractionError)):
        logger.warning("request_id=%s Extraction/validation error: %s", request_id, exc.message)
        return JSONResponse(
            status_code=422,
            content=_error_body(exc.message, exc.details),
        )

    # Catch-all for any other domain error
    logger.error("request_id=%s Unhandled domain error: %s", request_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=_error_body("An internal error occurred."),
    )


async def pydantic_validation_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """Handles Pydantic validation errors on request DTOs."""
    logger.warning("request_id=%s Request validation error", getattr(request.state, "request_id", "unknown"))
    # Use exc.json() via intermediate parse to guarantee JSON-safe serialization
    # (some pydantic error ctx values may contain non-serializable Python objects like ValueError)
    import json as _json
    try:
        errors = _json.loads(exc.json())
    except Exception:
        errors = str(exc)
    return JSONResponse(
        status_code=400,
        content=_error_body("Invalid request body.", errors),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for unexpected exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.critical("request_id=%s Unhandled exception: %s", request_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=_error_body("An unexpected internal error occurred."),
    )

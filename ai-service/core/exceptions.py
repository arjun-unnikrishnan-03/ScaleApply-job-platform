"""
Domain exception hierarchy for the AI Recruitment Platform.

All exceptions inherit from RecruitmentError to allow callers to
catch platform-wide failures with a single except clause, while
still being able to handle specific failure modes precisely.
"""


class RecruitmentError(Exception):
    """Root exception for the entire AI Recruitment Platform."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


# ──────────────────────────────────────────────
# Parser exceptions
# ──────────────────────────────────────────────

class ParseError(RecruitmentError):
    """Raised when a resume file cannot be read or decoded."""


class UnsupportedFileTypeError(ParseError):
    """Raised when the file extension has no registered parser."""

    def __init__(self, extension: str) -> None:
        super().__init__(
            message=f"No parser registered for file extension '{extension}'.",
            details={"extension": extension},
        )
        self.extension = extension


class EmptyDocumentError(ParseError):
    """Raised when the parsed file yields no usable text content."""

    def __init__(self, source_path: str) -> None:
        super().__init__(
            message=f"Document '{source_path}' produced no extractable text.",
            details={"source_path": source_path},
        )


# ──────────────────────────────────────────────
# Provider exceptions
# ──────────────────────────────────────────────

class ProviderError(RecruitmentError):
    """Raised when an LLM provider call fails."""


class ProviderNotFoundError(ProviderError):
    """Raised when the factory cannot locate a requested provider."""

    def __init__(self, provider_name: str, available: list[str]) -> None:
        super().__init__(
            message=(
                f"Provider '{provider_name}' is not registered. "
                f"Available providers: {available}."
            ),
            details={"provider_name": provider_name, "available": available},
        )


class ProviderResponseError(ProviderError):
    """Raised when the LLM returns an unexpected or unusable response."""


class ProviderRateLimitError(ProviderError):
    """Raised when the LLM API rate-limit is hit."""


class ProviderAuthError(ProviderError):
    """Raised when API credentials are missing or invalid."""


# ──────────────────────────────────────────────
# Gemini Specific Provider exceptions
# ──────────────────────────────────────────────

class GeminiProviderError(ProviderError):
    """Root exception for all Gemini SDK failures."""

class GeminiAuthenticationError(GeminiProviderError, ProviderAuthError):
    """Raised when the Gemini API key is invalid."""

class GeminiRateLimitError(GeminiProviderError, ProviderRateLimitError):
    """Raised when the Gemini API returns a 429 Resource Exhausted."""

class GeminiTimeoutError(GeminiProviderError):
    """Raised when the Gemini API request times out."""

# ──────────────────────────────────────────────
# Vector Store & Embedding exceptions
# ──────────────────────────────────────────────

class EmbeddingProviderError(ProviderError):
    """Raised when the embedding generation API fails."""

class QdrantConnectionError(RecruitmentError):
    """Raised when the Qdrant database cannot be reached."""

class QdrantSearchError(RecruitmentError):
    """Raised when a Qdrant search operation fails."""

# ──────────────────────────────────────────────
# Extraction / Validation exceptions
# ──────────────────────────────────────────────

class ExtractionError(RecruitmentError):
    """Raised when JSON cannot be extracted from the LLM response."""

    def __init__(self, raw_response: str) -> None:
        super().__init__(
            message="Failed to extract valid JSON from the LLM response.",
            details={"raw_response": raw_response[:500]},  # truncate for safety
        )


class ValidationError(RecruitmentError):
    """Raised when extracted data fails Pydantic domain model validation."""

    def __init__(self, pydantic_errors: list[dict]) -> None:
        super().__init__(
            message="Extracted candidate data failed schema validation.",
            details={"pydantic_errors": pydantic_errors},
        )

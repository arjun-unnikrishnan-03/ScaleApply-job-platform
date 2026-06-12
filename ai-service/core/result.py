"""
Result monad for clean error propagation.

Replaces bare exception-throwing with an explicit success/failure
discriminated union. This enables callers (future FastAPI endpoints,
queue consumers) to pattern-match on outcomes without try/except.

Usage:
    result = agent.process(path)

    if result.is_success:
        profile = result.value
    else:
        log.error(result.error)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from core.exceptions import RecruitmentError

T = TypeVar("T")  # Success value type
E = TypeVar("E", bound=RecruitmentError)  # Error type (constrained to domain errors)


@dataclass(frozen=True)
class AgentResult(Generic[T]):
    """
    Immutable result container.

    Exactly one of `value` or `error` will be set.
    `is_success` is the canonical discriminator.
    """

    is_success: bool
    value: T | None = field(default=None)
    error: RecruitmentError | None = field(default=None)
    metadata: dict = field(default_factory=dict)

    # ── Constructors ───────────────────────────────────────────────────────

    @classmethod
    def success(cls, value: T, metadata: dict | None = None) -> "AgentResult[T]":
        """Wrap a successful outcome."""
        return cls(is_success=True, value=value, metadata=metadata or {})

    @classmethod
    def failure(
        cls,
        error: RecruitmentError,
        metadata: dict | None = None,
    ) -> "AgentResult[T]":
        """Wrap a failed outcome."""
        return cls(is_success=False, error=error, metadata=metadata or {})

    # ── Convenience accessors ──────────────────────────────────────────────

    def unwrap(self) -> T:
        """
        Return the value or raise the wrapped error.

        Use only at application boundary where you want to escalate failures.
        """
        if self.is_success and self.value is not None:
            return self.value
        raise self.error or RuntimeError("AgentResult has no value and no error.")

    def __bool__(self) -> bool:
        return self.is_success

    def __repr__(self) -> str:
        if self.is_success:
            return f"AgentResult.success(value={self.value!r})"
        return f"AgentResult.failure(error={self.error!r})"

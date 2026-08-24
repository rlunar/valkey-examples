"""Shared rate-limiter contract."""

from __future__ import annotations

from typing import Protocol

from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy


class RateLimitDependencyError(RuntimeError):
    """Raised when Valkey cannot produce a trustworthy decision."""


class RateLimiter(Protocol):
    """Backend-independent rate-limiter interface."""

    def check(self, identity: str, policy: RateLimitPolicy, request_id: str) -> RateLimitDecision:
        """Admit or deny one request."""

    def ping(self) -> None:
        """Raise if Valkey is not ready."""

    def close(self) -> None:
        """Release backend resources."""

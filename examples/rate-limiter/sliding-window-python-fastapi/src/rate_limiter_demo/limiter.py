"""Shared rate-limiter contract."""

from __future__ import annotations

from typing import Protocol

from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy


class RateLimitDependencyError(RuntimeError):
    """Raised when Valkey cannot complete a rate-limit check."""


class RateLimiter(Protocol):
    """The methods every rate-limiter implementation must provide."""

    async def check(
        self, identity: str, policy: RateLimitPolicy, request_id: str
    ) -> RateLimitDecision:
        """Admit or deny one request."""

    async def ping(self) -> None:
        """Raise if Valkey is not ready."""

    async def close(self) -> None:
        """Release backend resources."""

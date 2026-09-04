"""Rate-limit policy and decision value objects."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """A named sliding-window policy."""

    policy_id: str
    limit: int
    window_ms: int


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """The complete result of one admission decision."""

    allowed: bool
    limit: int
    remaining: int
    reset_after_ms: int
    retry_after_ms: int

    @property
    def status_code(self) -> int:
        return 200 if self.allowed else 429

    @property
    def reset_after_seconds(self) -> int:
        return max(0, ceil(self.reset_after_ms / 1_000))

    @property
    def retry_after_seconds(self) -> int:
        return max(1, ceil(self.retry_after_ms / 1_000))

    def as_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_after_ms": self.reset_after_ms,
        }
        if not self.allowed:
            body["retry_after_ms"] = self.retry_after_ms
        return body

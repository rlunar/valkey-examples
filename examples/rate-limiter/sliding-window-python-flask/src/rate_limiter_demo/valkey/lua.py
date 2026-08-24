"""Server-side Lua sliding-window implementation."""

from __future__ import annotations

from importlib.resources import files
from threading import Lock

from glide_sync import GlideClient, Script

from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.limiter import RateLimitDependencyError
from rate_limiter_demo.valkey.common import integer_sequence, rate_limit_key


class LuaRateLimiter:
    """Use one cached server-side script for an atomic decision."""

    def __init__(self, client: GlideClient, key_prefix: str) -> None:
        self._client = client
        self._key_prefix = key_prefix
        script_text = (
            files("rate_limiter_demo.valkey.scripts")
            .joinpath("sliding_window.lua")
            .read_text(encoding="utf-8")
        )
        self._script = Script(script_text)  # type: ignore[no-untyped-call]
        self._connection_lock = Lock()

    def check(self, identity: str, policy: RateLimitPolicy, request_id: str) -> RateLimitDecision:
        key = rate_limit_key(self._key_prefix, policy, identity)
        try:
            with self._connection_lock:
                raw_result = self._client.invoke_script(
                    self._script,
                    keys=[key],
                    args=[str(policy.limit), str(policy.window_ms), request_id],
                )
            allowed, limit, remaining, reset_after_ms, retry_after_ms = integer_sequence(
                raw_result, 5
            )
        except Exception as error:
            raise RateLimitDependencyError("Valkey script could not produce a decision") from error

        return RateLimitDecision(
            allowed=bool(allowed),
            limit=limit,
            remaining=remaining,
            reset_after_ms=max(0, reset_after_ms),
            retry_after_ms=max(0, retry_after_ms),
        )

    def ping(self) -> None:
        self._client.ping()

    def close(self) -> None:
        self._client.close()

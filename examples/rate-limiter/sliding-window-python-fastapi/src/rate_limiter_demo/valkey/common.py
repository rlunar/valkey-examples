"""Shared Valkey helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from glide import GlideClient, GlideClientConfiguration, NodeAddress

from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.identity import hash_identity


async def create_glide_client(config: AppConfig) -> GlideClient:
    return await GlideClient.create(
        GlideClientConfiguration(
            addresses=[NodeAddress(config.valkey_host, config.valkey_port)],
            request_timeout=config.request_timeout_ms,
            client_name=f"valkey-example-rate-limiter-{config.implementation}",
        )
    )


def rate_limit_key(prefix: str, policy: RateLimitPolicy, identity: str) -> str:
    return f"{prefix}:{policy.policy_id}:{hash_identity(identity)}"


async def server_time_ms(client: GlideClient) -> int:
    seconds, microseconds = await client.time()
    return int(seconds) * 1_000 + int(microseconds) // 1_000


def oldest_score(value: Any, fallback: int) -> int:
    if isinstance(value, Mapping):
        scores = list(value.values())
        if scores:
            return int(float(scores[0]))
    return fallback


def integer_sequence(value: Any, expected: int) -> list[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("Valkey script returned a non-sequence response")
    if len(value) != expected:
        raise ValueError(f"Valkey script returned {len(value)} fields; expected {expected}")
    return [int(item) for item in value]


def build_decision(
    *,
    allowed: bool,
    policy: RateLimitPolicy,
    active_count: int,
    now_ms: int,
    oldest_ms: int,
) -> RateLimitDecision:
    reset_after_ms = max(0, oldest_ms + policy.window_ms - now_ms)
    remaining = max(0, policy.limit - active_count)
    return RateLimitDecision(
        allowed=allowed,
        limit=policy.limit,
        remaining=remaining,
        reset_after_ms=reset_after_ms,
        retry_after_ms=0 if allowed else max(1, reset_after_ms),
    )

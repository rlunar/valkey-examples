from __future__ import annotations

import asyncio
import uuid

import pytest

from rate_limiter_demo.decision import RateLimitPolicy
from rate_limiter_demo.valkey import create_glide_client
from rate_limiter_demo.valkey.common import rate_limit_key
from tests.conftest import build_limiter, make_test_config

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("implementation", ["multi-exec", "lua"])
async def test_concurrent_requests_never_over_admit(implementation: str) -> None:
    assert implementation in ("multi-exec", "lua")
    config = await make_test_config(implementation)  # type: ignore[arg-type]
    observer = await create_glide_client(config)
    await observer.custom_command(["FLUSHDB"])
    clients = [await create_glide_client(config) for _index in range(8)]
    limiters = [await build_limiter(config, client) for client in clients]
    policy = RateLimitPolicy("concurrent", limit=20, window_ms=5_000)

    async def invoke(index: int) -> bool:
        decision = await limiters[index % len(limiters)].check(
            "shared-identity", policy, uuid.uuid7().hex
        )
        return decision.allowed

    try:
        allowed = await asyncio.gather(*[invoke(i) for i in range(80)])

        assert sum(allowed) == policy.limit
        key = rate_limit_key(config.key_prefix, policy, "shared-identity")
        assert await observer.zcard(key) == policy.limit
    finally:
        for limiter in limiters:
            await limiter.close()
        await observer.close()

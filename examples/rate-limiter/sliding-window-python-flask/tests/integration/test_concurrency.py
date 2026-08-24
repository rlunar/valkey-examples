from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import cast

import pytest

from rate_limiter_demo.config import Implementation
from rate_limiter_demo.decision import RateLimitPolicy
from rate_limiter_demo.valkey import create_glide_client
from rate_limiter_demo.valkey.common import rate_limit_key
from tests.conftest import build_limiter, make_test_config

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("implementation", ["multi-exec", "lua"])
def test_concurrent_requests_never_over_admit(implementation: str) -> None:
    assert implementation in ("multi-exec", "lua")
    config = make_test_config(cast(Implementation, implementation))
    observer = create_glide_client(config)
    observer.custom_command(["FLUSHDB"])
    clients = [create_glide_client(config) for _index in range(8)]
    limiters = [build_limiter(config, client) for client in clients]
    policy = RateLimitPolicy("concurrent", limit=20, window_ms=5_000)

    def invoke(index: int) -> bool:
        decision = limiters[index % len(limiters)].check(
            "shared-identity", policy, uuid.uuid7().hex
        )
        return decision.allowed

    try:
        with ThreadPoolExecutor(max_workers=32) as executor:
            allowed = list(executor.map(invoke, range(80)))

        assert sum(allowed) == policy.limit
        key = rate_limit_key(config.key_prefix, policy, "shared-identity")
        assert observer.zcard(key) == policy.limit
    finally:
        for limiter in limiters:
            limiter.close()
        observer.close()

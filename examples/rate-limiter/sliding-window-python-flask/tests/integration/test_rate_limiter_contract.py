from __future__ import annotations

import time
import uuid

import pytest
from glide_sync import GlideClient

from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.decision import RateLimitPolicy
from rate_limiter_demo.limiter import RateLimiter
from rate_limiter_demo.valkey.common import rate_limit_key

pytestmark = pytest.mark.integration


def test_limit_identity_isolation_ttl_and_expiry(
    real_limiter: tuple[RateLimiter, GlideClient, AppConfig],
) -> None:
    limiter, observer, config = real_limiter
    policy = RateLimitPolicy("contract", limit=5, window_ms=300)

    decisions = [limiter.check("identity-a", policy, uuid.uuid4().hex) for _request in range(6)]

    assert [decision.allowed for decision in decisions] == [
        True,
        True,
        True,
        True,
        True,
        False,
    ]
    assert decisions[-1].remaining == 0
    assert 1 <= decisions[-1].retry_after_ms <= policy.window_ms

    isolated = limiter.check("identity-b", policy, uuid.uuid4().hex)
    assert isolated.allowed is True
    assert isolated.remaining == 4

    key = rate_limit_key(config.key_prefix, policy, "identity-a")
    assert observer.zcard(key) == policy.limit
    ttl = observer.pttl(key)
    assert 0 < ttl <= policy.window_ms

    time.sleep((decisions[-1].retry_after_ms + 50) / 1_000)
    after_window = limiter.check("identity-a", policy, uuid.uuid4().hex)
    assert after_window.allowed is True

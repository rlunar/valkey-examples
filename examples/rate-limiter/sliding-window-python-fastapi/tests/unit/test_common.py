from __future__ import annotations

import pytest

from rate_limiter_demo.decision import RateLimitPolicy
from rate_limiter_demo.valkey.common import (
    build_decision,
    integer_sequence,
    oldest_score,
    rate_limit_key,
)


def test_key_contains_policy_and_hash_not_raw_identity() -> None:
    policy = RateLimitPolicy("api", 5, 1_000)

    key = rate_limit_key("example", policy, "private-user")

    assert key.startswith("example:api:")
    assert "private-user" not in key


def test_oldest_score_reads_glide_mapping() -> None:
    assert oldest_score({b"request": 123.0}, 999) == 123
    assert oldest_score({}, 999) == 999


def test_integer_sequence_validates_script_contract() -> None:
    assert integer_sequence([1, b"2"], 2) == [1, 2]
    with pytest.raises(ValueError, match="non-sequence"):
        integer_sequence(b"12", 2)
    with pytest.raises(ValueError, match="expected 2"):
        integer_sequence([1], 2)


def test_build_decision_calculates_remaining_and_reset() -> None:
    policy = RateLimitPolicy("api", 5, 1_000)

    decision = build_decision(
        allowed=False,
        policy=policy,
        active_count=5,
        now_ms=2_000,
        oldest_ms=1_500,
    )

    assert decision.remaining == 0
    assert decision.reset_after_ms == 500
    assert decision.retry_after_ms == 500

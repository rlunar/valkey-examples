from rate_limiter_demo.decision import RateLimitDecision


def test_allowed_body_omits_retry_after() -> None:
    decision = RateLimitDecision(
        allowed=True,
        limit=5,
        remaining=4,
        reset_after_ms=1_001,
        retry_after_ms=0,
    )

    assert decision.status_code == 200
    assert decision.reset_after_seconds == 2
    assert decision.as_body() == {
        "allowed": True,
        "limit": 5,
        "remaining": 4,
        "reset_after_ms": 1_001,
    }


def test_denied_body_has_bounded_retry_after() -> None:
    decision = RateLimitDecision(
        allowed=False,
        limit=5,
        remaining=0,
        reset_after_ms=1,
        retry_after_ms=1,
    )

    assert decision.status_code == 429
    assert decision.retry_after_seconds == 1
    assert decision.as_body()["retry_after_ms"] == 1

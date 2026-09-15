from __future__ import annotations

import uuid
from dataclasses import dataclass

from rate_limiter_demo.app import create_app
from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.limiter import RateLimitDependencyError


@dataclass
class FakeLimiter:
    decision: RateLimitDecision | None = None
    dependency_failure: bool = False
    ready: bool = True

    def check(self, identity: str, policy: RateLimitPolicy, request_id: str) -> RateLimitDecision:
        if self.dependency_failure:
            raise RateLimitDependencyError("unavailable")
        assert identity
        assert uuid.UUID(hex=request_id).version == 7
        assert policy.limit == 5
        assert self.decision is not None
        return self.decision

    def ping(self) -> None:
        if not self.ready:
            raise RuntimeError("not ready")

    def close(self) -> None:
        pass


def test_allowed_response_exposes_rate_limit_headers() -> None:
    limiter = FakeLimiter(RateLimitDecision(True, 5, 4, 1_000, 0))
    client = create_app(AppConfig(), limiter).test_client()

    response = client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 200
    assert response.json["allowed"] is True
    assert response.headers["RateLimit-Remaining"] == "4"
    assert "Retry-After" not in response.headers


def test_denied_response_exposes_retry_after() -> None:
    limiter = FakeLimiter(RateLimitDecision(False, 5, 0, 501, 501))
    client = create_app(AppConfig(), limiter).test_client()

    response = client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.json["retry_after_ms"] == 501


def test_invalid_identity_is_bad_request() -> None:
    limiter = FakeLimiter(RateLimitDecision(True, 5, 4, 1_000, 0))
    client = create_app(AppConfig(), limiter).test_client()

    response = client.get("/api/limited")

    assert response.status_code == 400


def test_dependency_failure_is_service_unavailable() -> None:
    client = create_app(AppConfig(), FakeLimiter(dependency_failure=True)).test_client()

    response = client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 503


def test_health_endpoints_are_distinct() -> None:
    limiter = FakeLimiter(ready=False)
    client = create_app(AppConfig(), limiter).test_client()

    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    assert client.get("/").json["implementation"] == "multi-exec"

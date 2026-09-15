from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from rate_limiter_demo.app import create_app
from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.limiter import RateLimitDependencyError


class FakeLimiter:
    def __init__(
        self,
        decision: RateLimitDecision | None = None,
        dependency_failure: bool = False,
        ready: bool = True,
    ) -> None:
        self.decision = decision
        self.dependency_failure = dependency_failure
        self.ready = ready

    async def check(
        self, identity: str, policy: RateLimitPolicy, request_id: str
    ) -> RateLimitDecision:
        if self.dependency_failure:
            raise RateLimitDependencyError("unavailable")
        assert identity
        assert uuid.UUID(hex=request_id).version == 7
        assert policy.limit == 5
        assert self.decision is not None
        return self.decision

    async def ping(self) -> None:
        if not self.ready:
            raise RuntimeError("not ready")

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_allowed_response_exposes_rate_limit_headers() -> None:
    limiter = FakeLimiter(RateLimitDecision(True, 5, 4, 1_000, 0))
    app = create_app(AppConfig(), limiter)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert response.headers["RateLimit-Remaining"] == "4"
    assert "Retry-After" not in response.headers


@pytest.mark.asyncio
async def test_denied_response_exposes_retry_after() -> None:
    limiter = FakeLimiter(RateLimitDecision(False, 5, 0, 501, 501))
    app = create_app(AppConfig(), limiter)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.json()["retry_after_ms"] == 501


@pytest.mark.asyncio
async def test_invalid_identity_is_bad_request() -> None:
    limiter = FakeLimiter(RateLimitDecision(True, 5, 4, 1_000, 0))
    app = create_app(AppConfig(), limiter)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/limited")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_dependency_failure_is_service_unavailable() -> None:
    app = create_app(AppConfig(), FakeLimiter(dependency_failure=True))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/limited", headers={"X-Client-ID": "client-a"})

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_health_endpoints_are_distinct() -> None:
    limiter = FakeLimiter(ready=False)
    app = create_app(AppConfig(), limiter)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        live = await client.get("/health/live")
        ready = await client.get("/health/ready")
        index = await client.get("/")

    assert live.status_code == 200
    assert ready.status_code == 503
    assert index.json()["implementation"] == "multi-exec"

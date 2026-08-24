"""FastAPI HTTP adapter for the sliding-window rate limiter."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse

from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.identity import InvalidIdentity, normalize_identity
from rate_limiter_demo.limiter import RateLimitDependencyError, RateLimiter
from rate_limiter_demo.valkey import (
    LuaRateLimiter,
    MultiExecRateLimiter,
    create_glide_client,
)

LOGGER = logging.getLogger(__name__)


async def _build_limiter(config: AppConfig) -> RateLimiter:
    client = await create_glide_client(config)
    if config.implementation == "lua":
        return LuaRateLimiter(client, config.key_prefix)
    return MultiExecRateLimiter(client, config.key_prefix, config.max_retries)


def _decision_response(decision: RateLimitDecision) -> JSONResponse:
    headers: dict[str, str] = {
        "RateLimit-Limit": str(decision.limit),
        "RateLimit-Remaining": str(decision.remaining),
        "RateLimit-Reset": str(decision.reset_after_seconds),
    }
    if not decision.allowed:
        headers["Retry-After"] = str(decision.retry_after_seconds)
    return JSONResponse(
        content=decision.as_body(),
        status_code=decision.status_code,
        headers=headers,
    )


def create_app(config: AppConfig | None = None, limiter: RateLimiter | None = None) -> FastAPI:
    runtime_config = config or AppConfig()
    policy = RateLimitPolicy(
        policy_id=runtime_config.policy_id,
        limit=runtime_config.request_limit,
        window_ms=runtime_config.window_ms,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resolved_limiter: RateLimiter
        if limiter is not None:
            resolved_limiter = limiter
        else:
            resolved_limiter = await _build_limiter(runtime_config)
        application.state.limiter = resolved_limiter
        application.state.policy = policy
        LOGGER.info("Rate limiter started with implementation=%s", runtime_config.implementation)
        try:
            yield
        finally:
            await resolved_limiter.close()
            LOGGER.info("Rate limiter closed")

    app = FastAPI(
        title="Sliding-Window Rate Limiter",
        description="Valkey sorted-set rate limiter with WATCH/MULTI/EXEC and Lua backends.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Pre-populate state when a test limiter is injected so tests that skip
    # the lifespan (e.g. httpx ASGITransport) still find the state attributes.
    if limiter is not None:
        app.state.limiter = limiter
        app.state.policy = policy

    @app.get("/api/limited")
    async def limited(
        request: Request,
        x_client_id: str | None = Header(default=None),
    ) -> Response:
        try:
            identity = normalize_identity(x_client_id or "")
            decision = await request.app.state.limiter.check(
                identity, request.app.state.policy, uuid.uuid4().hex
            )
        except InvalidIdentity:
            return JSONResponse(
                content={"error": "X-Client-ID is missing or invalid"}, status_code=400
            )
        except RateLimitDependencyError:
            LOGGER.exception("Rate-limit dependency failed")
            return JSONResponse(
                content={"error": "rate-limit dependency unavailable"}, status_code=503
            )
        return _decision_response(decision)

    @app.get("/health/live")
    async def live() -> JSONResponse:
        return JSONResponse(content={"status": "ok"})

    @app.get("/health/ready")
    async def ready(request: Request) -> JSONResponse:
        try:
            await request.app.state.limiter.ping()
        except Exception:
            return JSONResponse(content={"status": "not-ready"}, status_code=503)
        return JSONResponse(content={"status": "ready"})

    @app.get("/")
    async def index() -> JSONResponse:
        body: dict[str, Any] = {
            "example": "sliding-window-rate-limiter",
            "implementation": runtime_config.implementation,
            "endpoint": "/api/limited",
        }
        return JSONResponse(content=body)

    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    config = AppConfig()
    app = create_app(config)
    LOGGER.info("Starting rate limiter with implementation=%s", config.implementation)
    uvicorn.run(app, host=config.app_host, port=config.app_port, log_level="info")


if __name__ == "__main__":
    main()

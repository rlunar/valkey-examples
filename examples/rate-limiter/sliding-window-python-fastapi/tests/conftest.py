"""Shared real-Valkey fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from glide import GlideClient

from rate_limiter_demo.config import AppConfig, Implementation
from rate_limiter_demo.limiter import RateLimiter
from rate_limiter_demo.valkey import (
    LuaRateLimiter,
    MultiExecRateLimiter,
    create_glide_client,
)


async def make_test_config(implementation: Implementation = "multi-exec") -> AppConfig:
    return AppConfig(
        implementation=implementation,
        request_limit=5,
        window_ms=1_000,
        max_retries=100,
        valkey_host=os.getenv("VALKEY_HOST", "127.0.0.1"),
        valkey_port=int(os.getenv("VALKEY_PORT", "6379")),
    )


async def build_limiter(config: AppConfig, client: GlideClient) -> RateLimiter:
    if config.implementation == "lua":
        return LuaRateLimiter(client, config.key_prefix)
    return MultiExecRateLimiter(client, config.key_prefix, config.max_retries)


@pytest.fixture(params=["multi-exec", "lua"])
async def real_limiter(
    request: pytest.FixtureRequest,
) -> AsyncIterator[tuple[RateLimiter, GlideClient, AppConfig]]:
    implementation = request.param
    assert implementation in ("multi-exec", "lua")
    config = await make_test_config(implementation)  # type: ignore[arg-type]
    observer = await create_glide_client(config)
    await observer.custom_command(["FLUSHDB"])
    limiter = await build_limiter(config, await create_glide_client(config))
    try:
        yield limiter, observer, config
    finally:
        await limiter.close()
        await observer.close()

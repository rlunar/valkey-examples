"""Shared real-Valkey fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from glide_sync import GlideClient

from rate_limiter_demo.config import AppConfig, Implementation
from rate_limiter_demo.limiter import RateLimiter
from rate_limiter_demo.valkey import (
    LuaRateLimiter,
    MultiExecRateLimiter,
    create_glide_client,
)


def make_test_config(implementation: Implementation = "multi-exec") -> AppConfig:
    return AppConfig(
        implementation=implementation,
        request_limit=5,
        window_ms=1_000,
        max_retries=100,
        valkey_host=os.getenv("VALKEY_HOST", "127.0.0.1"),
        valkey_port=int(os.getenv("VALKEY_PORT", "6379")),
    )


def build_limiter(config: AppConfig, client: GlideClient) -> RateLimiter:
    if config.implementation == "lua":
        return LuaRateLimiter(client, config.key_prefix)
    return MultiExecRateLimiter(client, config.key_prefix, config.max_retries)


@pytest.fixture(params=["multi-exec", "lua"])
def real_limiter(
    request: pytest.FixtureRequest,
) -> Iterator[tuple[RateLimiter, GlideClient, AppConfig]]:
    implementation = request.param
    assert implementation in ("multi-exec", "lua")
    config = make_test_config(implementation)
    observer = create_glide_client(config)
    observer.custom_command(["FLUSHDB"])
    limiter = build_limiter(config, create_glide_client(config))
    try:
        yield limiter, observer, config
    finally:
        limiter.close()
        observer.close()

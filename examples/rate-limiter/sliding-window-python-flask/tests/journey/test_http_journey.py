from __future__ import annotations

import pytest
from glide_sync import GlideClient

from rate_limiter_demo.app import create_app
from rate_limiter_demo.config import AppConfig
from rate_limiter_demo.limiter import RateLimiter

pytestmark = pytest.mark.journey


def test_http_journey_has_allowed_denied_and_isolated_responses(
    real_limiter: tuple[RateLimiter, GlideClient, AppConfig],
) -> None:
    limiter, _observer, base_config = real_limiter
    config = AppConfig(
        implementation=base_config.implementation,
        request_limit=3,
        window_ms=1_000,
        key_prefix=base_config.key_prefix,
    )
    client = create_app(config, limiter).test_client()

    allowed = [
        client.get("/api/limited", headers={"X-Client-ID": "journey-a"}) for _request in range(3)
    ]
    denied = client.get("/api/limited", headers={"X-Client-ID": "journey-a"})
    isolated = client.get("/api/limited", headers={"X-Client-ID": "journey-b"})

    assert [response.status_code for response in allowed] == [200, 200, 200]
    assert denied.status_code == 429
    assert int(denied.headers["Retry-After"]) >= 1
    assert isolated.status_code == 200

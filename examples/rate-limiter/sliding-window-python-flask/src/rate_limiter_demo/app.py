"""Flask HTTP adapter for the sliding-window rate limiter."""

from __future__ import annotations

import atexit
import logging
import uuid
from typing import Any

from flask import Flask, Response, jsonify, request

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


def _build_limiter(config: AppConfig) -> RateLimiter:
    client = create_glide_client(config)
    if config.implementation == "lua":
        return LuaRateLimiter(client, config.key_prefix)
    return MultiExecRateLimiter(client, config.key_prefix, config.max_retries)


def _decision_response(decision: RateLimitDecision) -> tuple[Response, int]:
    response = jsonify(decision.as_body())
    response.headers["RateLimit-Limit"] = str(decision.limit)
    response.headers["RateLimit-Remaining"] = str(decision.remaining)
    response.headers["RateLimit-Reset"] = str(decision.reset_after_seconds)
    if not decision.allowed:
        response.headers["Retry-After"] = str(decision.retry_after_seconds)
    return response, decision.status_code


def create_app(config: AppConfig | None = None, limiter: RateLimiter | None = None) -> Flask:
    runtime_config = config or AppConfig()
    runtime_limiter = limiter or _build_limiter(runtime_config)
    policy = RateLimitPolicy(
        policy_id=runtime_config.policy_id,
        limit=runtime_config.request_limit,
        window_ms=runtime_config.window_ms,
    )

    app = Flask(__name__)
    app.config["RATE_LIMITER_CONFIG"] = runtime_config
    app.extensions["rate_limiter"] = runtime_limiter
    app.extensions["rate_limit_policy"] = policy

    @app.get("/api/limited")
    def limited() -> tuple[Response, int]:
        try:
            identity = normalize_identity(request.headers.get("X-Client-ID", ""))
            decision = runtime_limiter.check(identity, policy, uuid.uuid7().hex)
        except InvalidIdentity as error:
            return jsonify({"error": str(error)}), 400
        except RateLimitDependencyError:
            LOGGER.exception("Rate-limit dependency failed")
            return jsonify({"error": "rate-limit dependency unavailable"}), 503
        return _decision_response(decision)

    @app.get("/health/live")
    def live() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200

    @app.get("/health/ready")
    def ready() -> tuple[Response, int]:
        try:
            runtime_limiter.ping()
        except Exception:
            return jsonify({"status": "not-ready"}), 503
        return jsonify({"status": "ready"}), 200

    @app.get("/")
    def index() -> tuple[Response, int]:
        body: dict[str, Any] = {
            "example": "sliding-window-rate-limiter",
            "implementation": runtime_config.implementation,
            "endpoint": "/api/limited",
        }
        return jsonify(body), 200

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = AppConfig()
    app = create_app(config)
    limiter = app.extensions["rate_limiter"]
    atexit.register(limiter.close)
    LOGGER.info("Starting rate limiter with implementation=%s", config.implementation)
    app.run(host=config.flask_host, port=config.flask_port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

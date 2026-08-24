"""Environment-backed application configuration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal, cast

Implementation = Literal["multi-exec", "lua"]

_POLICY_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class ConfigurationError(ValueError):
    """Raised when an environment value is invalid."""


def _integer(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from error
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}, got {value}")
    return value


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated runtime settings."""

    implementation: Implementation = "multi-exec"
    request_limit: int = 5
    window_ms: int = 10_000
    policy_id: str = "default"
    key_prefix: str = "valkey-examples:rate-limit:v1"
    max_retries: int = 50
    valkey_host: str = "127.0.0.1"
    valkey_port: int = 6379
    request_timeout_ms: int = 1_000
    flask_host: str = "127.0.0.1"
    flask_port: int = 8000

    def __post_init__(self) -> None:
        if self.implementation not in ("multi-exec", "lua"):
            raise ConfigurationError("RATE_LIMIT_IMPLEMENTATION must be 'multi-exec' or 'lua'")
        if not 1 <= self.request_limit <= 100_000:
            raise ConfigurationError("request_limit must be between 1 and 100000")
        if not 100 <= self.window_ms <= 86_400_000:
            raise ConfigurationError("window_ms must be between 100 and 86400000")
        if not _POLICY_ID.fullmatch(self.policy_id):
            raise ConfigurationError(
                "RATE_LIMIT_POLICY_ID must be a lowercase slug of at most 64 characters"
            )
        if not self.key_prefix or len(self.key_prefix) > 128:
            raise ConfigurationError("RATE_LIMIT_KEY_PREFIX must contain 1 to 128 characters")
        if not 1 <= self.max_retries <= 100:
            raise ConfigurationError("max_retries must be between 1 and 100")
        if not self.valkey_host:
            raise ConfigurationError("VALKEY_HOST must not be empty")
        if not 1 <= self.valkey_port <= 65_535:
            raise ConfigurationError("valkey_port must be between 1 and 65535")
        if not 50 <= self.request_timeout_ms <= 30_000:
            raise ConfigurationError("request_timeout_ms must be between 50 and 30000")
        if not self.flask_host:
            raise ConfigurationError("FLASK_HOST must not be empty")
        if not 1 <= self.flask_port <= 65_535:
            raise ConfigurationError("flask_port must be between 1 and 65535")

    @classmethod
    def from_env(cls) -> AppConfig:
        implementation = os.getenv("RATE_LIMIT_IMPLEMENTATION", "multi-exec")
        if implementation not in ("multi-exec", "lua"):
            raise ConfigurationError("RATE_LIMIT_IMPLEMENTATION must be 'multi-exec' or 'lua'")
        return cls(
            implementation=cast(Implementation, implementation),
            request_limit=_integer("RATE_LIMIT_REQUESTS", 5, 1, 100_000),
            window_ms=_integer("RATE_LIMIT_WINDOW_MS", 10_000, 100, 86_400_000),
            policy_id=os.getenv("RATE_LIMIT_POLICY_ID", "default"),
            key_prefix=os.getenv("RATE_LIMIT_KEY_PREFIX", "valkey-examples:rate-limit:v1"),
            max_retries=_integer("RATE_LIMIT_MAX_RETRIES", 50, 1, 100),
            valkey_host=os.getenv("VALKEY_HOST", "127.0.0.1"),
            valkey_port=_integer("VALKEY_PORT", 6379, 1, 65_535),
            request_timeout_ms=_integer("VALKEY_REQUEST_TIMEOUT_MS", 1_000, 50, 30_000),
            flask_host=os.getenv("FLASK_HOST", "127.0.0.1"),
            flask_port=_integer("FLASK_PORT", 8000, 1, 65_535),
        )

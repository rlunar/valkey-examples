"""Environment-backed application configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Implementation = Literal["multi-exec", "lua"]


class AppConfig(BaseSettings):
    """Validated, immutable runtime settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    implementation: Implementation = Field(
        default="multi-exec", validation_alias="RATE_LIMIT_IMPLEMENTATION"
    )
    request_limit: int = Field(default=5, ge=1, le=100_000, validation_alias="RATE_LIMIT_REQUESTS")
    window_ms: int = Field(
        default=10_000,
        ge=100,
        le=86_400_000,
        validation_alias="RATE_LIMIT_WINDOW_MS",
    )
    policy_id: str = Field(
        default="default",
        pattern=r"^[a-z0-9][a-z0-9-]{0,63}$",
        validation_alias="RATE_LIMIT_POLICY_ID",
    )
    key_prefix: str = Field(
        default="valkey-examples:rate-limit:v1",
        min_length=1,
        max_length=128,
        validation_alias="RATE_LIMIT_KEY_PREFIX",
    )
    max_retries: int = Field(default=50, ge=1, le=100, validation_alias="RATE_LIMIT_MAX_RETRIES")
    valkey_host: str = Field(default="127.0.0.1", min_length=1, validation_alias="VALKEY_HOST")
    valkey_port: int = Field(default=6379, ge=1, le=65_535, validation_alias="VALKEY_PORT")
    request_timeout_ms: int = Field(
        default=1_000,
        ge=50,
        le=30_000,
        validation_alias="VALKEY_REQUEST_TIMEOUT_MS",
    )
    app_host: str = Field(default="127.0.0.1", min_length=1, validation_alias="APP_HOST")
    app_port: int = Field(default=8000, ge=1, le=65_535, validation_alias="APP_PORT")

"""Validated environment-backed configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

type Address = tuple[str, int]


class Topology(StrEnum):
    """Valkey deployment shape selected by the application."""

    STANDALONE = "standalone"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


class AppSettings(BaseSettings):
    """Immutable application and Valkey settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    topology: Topology = Field(
        default=Topology.STANDALONE,
        validation_alias="VALKEY_TOPOLOGY",
    )
    valkey_addresses: str = Field(
        default="127.0.0.1:6379",
        min_length=3,
        max_length=2048,
        validation_alias="VALKEY_ADDRESSES",
    )
    sentinel_master: str = Field(
        default="demo-primary",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$",
        validation_alias="VALKEY_SENTINEL_MASTER",
    )
    database_id: int = Field(
        default=0,
        ge=0,
        le=15,
        validation_alias="VALKEY_DATABASE_ID",
    )
    request_timeout_ms: int = Field(
        default=1_000,
        ge=50,
        le=30_000,
        validation_alias="VALKEY_REQUEST_TIMEOUT_MS",
    )
    connection_timeout_ms: int = Field(
        default=2_000,
        ge=100,
        le=30_000,
        validation_alias="VALKEY_CONNECTION_TIMEOUT_MS",
    )
    key_prefix: str = Field(
        default="valkey-examples:flask-base:v1",
        pattern=r"^[a-z0-9][a-z0-9:._-]{0,127}$",
        validation_alias="VALKEY_KEY_PREFIX",
    )

    flask_host: str = Field(
        default="127.0.0.1",
        min_length=1,
        validation_alias="FLASK_HOST",
    )
    flask_port: int = Field(
        default=8000,
        ge=1,
        le=65_535,
        validation_alias="FLASK_PORT",
    )
    flask_threads: int = Field(
        default=4,
        ge=1,
        le=64,
        validation_alias="FLASK_THREADS",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    otel_enabled: bool = Field(default=True, validation_alias="OTEL_ENABLED")
    otel_service_name: str = Field(
        default="valkey-flask-demo",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$",
        validation_alias="OTEL_SERVICE_NAME",
    )
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    @model_validator(mode="after")
    def validate_topology_settings(self) -> Self:
        self.addresses()
        if self.topology is Topology.CLUSTER and self.database_id != 0:
            raise ValueError("Valkey Cluster supports only database 0")
        if self.otel_exporter_otlp_endpoint is not None:
            endpoint = self.otel_exporter_otlp_endpoint
            if not endpoint.startswith(("http://", "https://")):
                raise ValueError("OTEL_EXPORTER_OTLP_ENDPOINT must use http:// or https://")
        return self

    def addresses(self) -> tuple[Address, ...]:
        """Parse and validate comma-separated host:port addresses."""

        raw_addresses = [item.strip() for item in self.valkey_addresses.split(",")]
        if not raw_addresses or any(not item for item in raw_addresses):
            raise ValueError("VALKEY_ADDRESSES must contain host:port entries")
        if len(raw_addresses) > 32:
            raise ValueError("VALKEY_ADDRESSES supports at most 32 entries")
        return tuple(self._parse_address(item) for item in raw_addresses)

    @staticmethod
    def _parse_address(value: str) -> Address:
        if value.startswith("["):
            closing = value.find("]")
            if closing < 2 or value[closing + 1 : closing + 2] != ":":
                raise ValueError(f"Invalid bracketed address: {value}")
            host = value[1:closing]
            port_text = value[closing + 2 :]
        else:
            host, separator, port_text = value.rpartition(":")
            if not separator:
                raise ValueError(f"Address must include a port: {value}")

        if not host or any(character.isspace() for character in host):
            raise ValueError(f"Invalid address host: {value}")
        try:
            port = int(port_text)
        except ValueError as error:
            raise ValueError(f"Invalid address port: {value}") from error
        if not 1 <= port <= 65_535:
            raise ValueError(f"Address port is out of range: {value}")
        return host, port

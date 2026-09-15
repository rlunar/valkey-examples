"""Configuration unit tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from valkey_flask_demo.config import AppSettings, Topology


def test_defaults_are_safe_for_direct_local_execution() -> None:
    settings = AppSettings(_env_file=None)

    assert settings.topology is Topology.STANDALONE
    assert settings.addresses() == (("127.0.0.1", 6379),)
    assert settings.flask_host == "127.0.0.1"


def test_multiple_and_ipv6_addresses_are_parsed() -> None:
    settings = AppSettings(
        _env_file=None,
        valkey_addresses="node-1:6379,[::1]:6380",
    )

    assert settings.addresses() == (("node-1", 6379), ("::1", 6380))


@pytest.mark.parametrize(
    "address",
    ["node", "node:not-a-port", "node:0", ":6379", "node:70000", "node:6379,"],
)
def test_invalid_addresses_fail_before_network_access(address: str) -> None:
    with pytest.raises(ValidationError):
        AppSettings(_env_file=None, valkey_addresses=address)


def test_cluster_rejects_nonzero_database() -> None:
    with pytest.raises(ValidationError, match="database 0"):
        AppSettings(
            _env_file=None,
            topology=Topology.CLUSTER,
            database_id=1,
        )


def test_otlp_endpoint_requires_http() -> None:
    with pytest.raises(ValidationError, match="http"):
        AppSettings(
            _env_file=None,
            otel_exporter_otlp_endpoint="collector:4318",
        )

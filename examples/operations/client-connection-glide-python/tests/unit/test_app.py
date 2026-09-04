"""Behavior tests for the minimal application."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from valkey_connection.app import create_client, run


class FakeClient:
    """The Valkey boundary needed by the public run function."""

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value.encode()

    def get(self, key: str) -> bytes | None:
        return self.values.get(key)


def test_run_stores_retrieves_and_prints_the_configured_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("VALKEY_MESSAGE", "hello from the test")

    result = run(FakeClient())

    assert result == "hello from the test"
    assert capsys.readouterr().out == "hello from the test\n"


@patch("valkey_connection.app.GlideClient.create")
def test_create_client_connects_to_the_standalone_addresses(
    create: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VALKEY_MODE", "standalone")
    monkeypatch.setenv("VALKEY_ADDRESSES", "valkey:6379")

    client = create_client()

    config = create.call_args.args[0]
    assert [(address.host, address.port) for address in config.addresses] == [("valkey", 6379)]
    assert client is create.return_value


@patch("valkey_connection.app.GlideClusterClient.create")
def test_create_client_connects_to_the_cluster_seed_addresses(
    create: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VALKEY_MODE", "cluster")
    monkeypatch.setenv(
        "VALKEY_ADDRESSES",
        "node-1:6379,node-2:6379,node-3:6379",
    )

    client = create_client()

    config = create.call_args.args[0]
    assert [(address.host, address.port) for address in config.addresses] == [
        ("node-1", 6379),
        ("node-2", 6379),
        ("node-3", 6379),
    ]
    assert client is create.return_value

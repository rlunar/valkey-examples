"""Unit tests for GLIDE client selection."""

from __future__ import annotations

from unittest.mock import Mock, patch

from valkey_quickstart.valkey_client import ValkeyClient


@patch("valkey_quickstart.valkey_client.GlideClient.create")
def test_standalone_client_uses_all_addresses(create: Mock, monkeypatch: object) -> None:
    monkeypatch.setenv("VALKEY_MODE", "standalone")
    monkeypatch.setenv("VALKEY_ADDRESSES", "primary:6379,replica:6380")

    valkey = ValkeyClient()

    config = create.call_args.args[0]
    assert [(address.host, address.port) for address in config.addresses] == [
        ("primary", 6379),
        ("replica", 6380),
    ]
    assert valkey.client is create.return_value


@patch("valkey_quickstart.valkey_client.GlideClusterClient.create")
def test_cluster_client_uses_seed_addresses(create: Mock, monkeypatch: object) -> None:
    monkeypatch.setenv("VALKEY_MODE", "cluster")
    monkeypatch.setenv("VALKEY_ADDRESSES", "node-1:6379,node-2:6379,node-3:6379")

    valkey = ValkeyClient()

    config = create.call_args.args[0]
    assert [(address.host, address.port) for address in config.addresses] == [
        ("node-1", 6379),
        ("node-2", 6379),
        ("node-3", 6379),
    ]
    assert valkey.client is create.return_value

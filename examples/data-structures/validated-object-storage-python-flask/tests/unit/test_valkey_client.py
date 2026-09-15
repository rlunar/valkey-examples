"""Unit tests for typed Valkey serialization."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import Mock, patch
from uuid import UUID

from pytest import MonkeyPatch

from validated_objects.models import PRODUCT_ADAPTER, PhysicalProduct
from validated_objects.valkey_client import ValkeyClient

PRODUCT_ID = UUID("11111111-1111-4111-8111-111111111111")


class FakeGlideClient:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}
        self.closed = False

    def set(self, key: str, value: bytes) -> str:
        self.values[key] = value
        return "OK"

    def get(self, key: str) -> bytes | None:
        return self.values.get(key)

    def delete(self, keys: list[str]) -> int:
        return sum(self.values.pop(key, None) is not None for key in keys)

    def close(self) -> None:
        self.closed = True


def test_typed_save_get_and_delete() -> None:
    valkey = object.__new__(ValkeyClient)
    client = FakeGlideClient()
    valkey.client = cast(Any, client)
    product = PRODUCT_ADAPTER.validate_python(
        {
            "kind": "physical",
            "id": str(PRODUCT_ID),
            "name": "Mechanical Keyboard",
            "price": "129.90",
            "active": True,
            "tags": ["hardware"],
            "created_at": "2026-09-03T12:00:00Z",
            "stock": 12,
            "weight_grams": 850,
        }
    )

    valkey.save(product)
    stored = valkey.get(PRODUCT_ID)

    assert isinstance(stored, PhysicalProduct)
    assert stored == product
    assert valkey.delete(PRODUCT_ID)
    assert valkey.get(PRODUCT_ID) is None
    valkey.close()
    assert client.closed


@patch("validated_objects.valkey_client.GlideClient.create")
def test_standalone_client_uses_all_addresses(create: Mock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("VALKEY_MODE", "standalone")
    monkeypatch.setenv("VALKEY_ADDRESSES", "primary:6379,replica:6380")

    valkey = ValkeyClient()

    config = create.call_args.args[0]
    assert [(address.host, address.port) for address in config.addresses] == [
        ("primary", 6379),
        ("replica", 6380),
    ]
    assert valkey.client is create.return_value


@patch("validated_objects.valkey_client.GlideClusterClient.create")
def test_cluster_client_uses_seed_addresses(create: Mock, monkeypatch: MonkeyPatch) -> None:
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

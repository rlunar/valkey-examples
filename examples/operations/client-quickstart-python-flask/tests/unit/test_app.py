"""Unit tests for the minimal Flask route."""

from __future__ import annotations

from typing import Any

from valkey_quickstart.app import DEMO_KEY, create_app


class FakeGlideClient:
    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def set(self, key: str, value: str) -> str:
        self.values[key] = value.encode()
        return "OK"

    def get(self, key: str) -> bytes | None:
        return self.values.get(key)

    def delete(self, keys: list[str]) -> int:
        return sum(self.values.pop(key, None) is not None for key in keys)


class FakeValkeyClient:
    def __init__(self) -> None:
        self.client = FakeGlideClient()


def test_store_retrieve_and_delete() -> None:
    valkey: Any = FakeValkeyClient()
    client = create_app(valkey).test_client()

    assert client.post("/value", json={"value": "hello"}).get_json() == {"value": "hello"}
    assert valkey.client.values[DEMO_KEY] == b"hello"
    assert client.get("/value").get_json() == {"value": "hello"}
    assert client.delete("/value").get_json() == {"deleted": True}
    assert client.get("/value").get_json() == {"value": None}

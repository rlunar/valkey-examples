"""ValkeyStore unit tests with fake GLIDE clients."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from glide_sync import ConnectionError, NodeDiscoveryMode

from valkey_flask_demo.config import AppSettings, Topology
from valkey_flask_demo.store import ValkeyStore


class FakeClient:
    def __init__(
        self,
        *,
        sentinel_response: object = None,
        fail_first_increment: bool = False,
    ) -> None:
        self.sentinel_response = sentinel_response
        self.fail_first_increment = fail_first_increment
        self.values: dict[str, int] = {}
        self.closed = False

    def custom_command(self, _command: list[str]) -> object:
        return self.sentinel_response

    def get(self, key: str) -> bytes | None:
        value = self.values.get(key)
        return str(value).encode() if value is not None else None

    def incr(self, key: str) -> int:
        if self.fail_first_increment:
            self.fail_first_increment = False
            raise ConnectionError("disconnected")
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def delete(self, keys: list[str]) -> int:
        return sum(self.values.pop(key, None) is not None for key in keys)

    def ping(self) -> bytes:
        return b"PONG"

    def close(self) -> None:
        self.closed = True


def client_factory(clients: list[FakeClient]) -> Iterator[FakeClient]:
    yield from clients


def test_standalone_uses_standard_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[object] = []
    fake = FakeClient()

    def create(config: object) -> FakeClient:
        captured.append(config)
        return fake

    monkeypatch.setattr("valkey_flask_demo.store.GlideClient.create", create)
    store = ValkeyStore(AppSettings(_env_file=None))

    assert captured[0].node_discovery_mode is NodeDiscoveryMode.STANDARD
    assert store.increment("demo") == 1
    assert store.get("demo") == 1
    assert store.delete("demo") is True
    store.ping()
    store.close()
    assert fake.closed


def test_cluster_uses_cluster_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeClient()
    captured: list[object] = []

    def create(config: object) -> FakeClient:
        captured.append(config)
        return fake

    monkeypatch.setattr("valkey_flask_demo.store.GlideClusterClient.create", create)
    settings = AppSettings(
        _env_file=None,
        topology=Topology.CLUSTER,
        valkey_addresses="node-1:6379,node-2:6379",
    )
    store = ValkeyStore(settings)

    assert len(captured[0].addresses) == 2
    assert store.topology_snapshot().client == "GlideClusterClient"


def test_sentinel_discovers_primary_and_reconnects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel_one = FakeClient(sentinel_response=[b"primary-1", b"6379"])
    data_one = FakeClient(fail_first_increment=True)
    sentinel_two = FakeClient(sentinel_response=[b"primary-2", b"6380"])
    data_two = FakeClient()
    clients = iter([sentinel_one, data_one, sentinel_two, data_two])
    configurations: list[object] = []

    def create(config: object) -> FakeClient:
        configurations.append(config)
        return next(clients)

    monkeypatch.setattr("valkey_flask_demo.store.GlideClient.create", create)
    settings = AppSettings(
        _env_file=None,
        topology=Topology.SENTINEL,
        valkey_addresses="sentinel-1:26379",
    )
    store = ValkeyStore(settings)

    assert store.increment("demo") == 1
    snapshot = store.topology_snapshot()
    assert snapshot.discovered_primary == "primary-2:6380"
    assert data_one.closed
    assert configurations[0].node_discovery_mode is NodeDiscoveryMode.STATIC
    assert configurations[1].node_discovery_mode is NodeDiscoveryMode.STATIC


@pytest.mark.parametrize(
    "response",
    [None, [], [b"host"], [b"host", b"invalid"], b"host:6379"],
)
def test_invalid_sentinel_responses_are_rejected(response: object) -> None:
    with pytest.raises(ValueError):
        ValkeyStore._parse_sentinel_response(response)

"""Flask adapter unit tests."""

from __future__ import annotations

from valkey_flask_demo.app import create_app
from valkey_flask_demo.config import AppSettings, Topology
from valkey_flask_demo.models import TopologySnapshot


class FakeStore:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.closed = False

    def get(self, name: str) -> int:
        return self.values.get(name, 0)

    def increment(self, name: str) -> int:
        value = self.get(name) + 1
        self.values[name] = value
        return value

    def delete(self, name: str) -> bool:
        return self.values.pop(name, None) is not None

    def ping(self) -> None:
        return None

    def topology_snapshot(self) -> TopologySnapshot:
        return TopologySnapshot(
            topology=Topology.STANDALONE,
            configured_addresses=("fake:6379",),
            client="FakeStore",
        )

    def close(self) -> None:
        self.closed = True


def build_client() -> tuple[FakeStore, object]:
    store = FakeStore()
    settings = AppSettings(_env_file=None, otel_enabled=False)
    app = create_app(settings, store)
    app.testing = True
    return store, app.test_client()


def test_counter_journey_uses_the_store_interface() -> None:
    store, client = build_client()

    assert client.get("/api/counters/demo").get_json()["value"] == 0
    assert client.post("/api/counters/demo").get_json()["value"] == 1
    assert client.post("/api/counters/demo").get_json()["value"] == 2
    assert client.delete("/api/counters/demo").get_json()["value"] == 0
    assert store.values == {}


def test_invalid_counter_name_is_rejected() -> None:
    _store, client = build_client()

    response = client.get("/api/counters/NOT-VALID")

    assert response.status_code == 400
    assert response.get_json() == {"error": "counter name must match [a-z0-9][a-z0-9_-]{0,63}"}


def test_health_and_topology_routes() -> None:
    _store, client = build_client()

    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").get_json()["status"] == "ready"
    assert client.get("/api/topology").get_json()["client"] == "FakeStore"
    assert client.get("/").get_json()["topology"] == "standalone"
    assert client.get("/health/live").headers["X-Request-ID"]

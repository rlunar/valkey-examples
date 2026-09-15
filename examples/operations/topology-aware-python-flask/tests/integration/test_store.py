"""Real-Valkey contract shared by every Compose topology."""

from __future__ import annotations

import uuid

import pytest

from valkey_flask_demo.config import AppSettings
from valkey_flask_demo.store import ValkeyStore


@pytest.mark.integration
def test_counter_store_contract_against_selected_topology() -> None:
    settings = AppSettings()
    store = ValkeyStore(settings)
    name = f"integration_{uuid.uuid7().hex}"

    try:
        store.ping()
        assert store.get(name) == 0
        assert store.increment(name) == 1
        assert store.increment(name) == 2
        assert store.get(name) == 2
        assert store.delete(name) is True
        assert store.get(name) == 0
        assert store.topology_snapshot().topology is settings.topology
    finally:
        store.delete(name)
        store.close()

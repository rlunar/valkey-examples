"""HTTP journey against the running Flask application and real Valkey."""

from __future__ import annotations

import os
import uuid

import httpx
import pytest


@pytest.mark.journey
def test_http_counter_journey() -> None:
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    expected_topology = os.environ["EXPECTED_TOPOLOGY"]
    name = f"journey_{uuid.uuid7().hex}"

    with httpx.Client(base_url=base_url, timeout=5) as client:
        readiness = client.get("/health/ready")
        assert readiness.status_code == 200
        assert readiness.json()["topology"] == expected_topology

        topology = client.get("/api/topology")
        assert topology.status_code == 200
        assert topology.json()["topology"] == expected_topology

        assert client.get(f"/api/counters/{name}").json()["value"] == 0
        assert client.post(f"/api/counters/{name}").json()["value"] == 1
        assert client.post(f"/api/counters/{name}").json()["value"] == 2
        assert client.delete(f"/api/counters/{name}").json()["value"] == 0
        assert client.get(f"/api/counters/{name}").json()["value"] == 0

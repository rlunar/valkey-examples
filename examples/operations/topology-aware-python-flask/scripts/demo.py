#!/usr/bin/env python3
"""Run the visible HTTP demo journey."""

from __future__ import annotations

import os

import httpx


def main() -> None:
    port = os.getenv("FLASK_PORT", "8000")
    base_url = os.getenv("BASE_URL", f"http://127.0.0.1:{port}")
    expected_topology = os.getenv("TOPOLOGY", "standalone")

    with httpx.Client(base_url=base_url, timeout=5) as client:
        topology = client.get("/api/topology")
        topology.raise_for_status()
        topology_body = topology.json()
        if topology_body["topology"] != expected_topology:
            raise SystemExit(
                f"Expected topology {expected_topology}; received {topology_body['topology']}"
            )

        client.delete("/api/counters/demo").raise_for_status()
        first = client.post("/api/counters/demo")
        first.raise_for_status()
        second = client.post("/api/counters/demo")
        second.raise_for_status()
        current = client.get("/api/counters/demo")
        current.raise_for_status()

        print(f"Topology: {topology_body['topology']}")
        print(f"GLIDE client: {topology_body['client']}")
        if topology_body.get("discovered_primary"):
            print(f"Sentinel primary: {topology_body['discovered_primary']}")
        print(f"Counter values: {first.json()['value']} -> {second.json()['value']}")
        print(f"Stored value: {current.json()['value']}")


if __name__ == "__main__":
    main()

"""Real-Valkey checks for the configured GLIDE client."""

import os

from valkey_quickstart.app import DEMO_KEY
from valkey_quickstart.valkey_client import ValkeyClient


def decode(response: object) -> str:
    assert isinstance(response, bytes)
    return response.decode()


def test_set_get_and_delete_against_real_valkey() -> None:
    valkey = ValkeyClient()
    try:
        valkey.client.set(DEMO_KEY, "integration")
        assert valkey.client.get(DEMO_KEY) == b"integration"
        assert valkey.client.delete([DEMO_KEY]) == 1
        assert valkey.client.get(DEMO_KEY) is None
    finally:
        valkey.close()


def test_expected_topology_shape() -> None:
    valkey = ValkeyClient()
    try:
        if os.environ["VALKEY_MODE"] == "cluster":
            nodes = decode(valkey.client.custom_command(["CLUSTER", "NODES"]))
            masters = [line for line in nodes.splitlines() if "master" in line.split()[2]]
            replicas = [line for line in nodes.splitlines() if "slave" in line.split()[2]]
            assert len(masters) == 3
            assert len(replicas) == 3
        else:
            replication = decode(valkey.client.custom_command(["INFO", "replication"]))
            assert "role:master" in replication
            assert "connected_slaves:1" in replication
    finally:
        valkey.close()

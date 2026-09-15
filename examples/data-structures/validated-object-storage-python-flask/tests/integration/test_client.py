"""Real-Valkey checks for typed product persistence."""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from validated_objects.models import DigitalProduct, PhysicalProduct
from validated_objects.valkey_client import ValkeyClient

PHYSICAL_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
DIGITAL_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def physical_product() -> PhysicalProduct:
    return PhysicalProduct(
        kind="physical",
        id=PHYSICAL_ID,
        name="Mechanical Keyboard",
        price=Decimal("129.90"),
        active=True,
        tags=("hardware", "keyboard"),
        created_at=datetime.fromisoformat("2026-09-03T12:00:00+00:00"),
        stock=12,
        weight_grams=850,
    )


def digital_product() -> DigitalProduct:
    return DigitalProduct(
        kind="digital",
        id=DIGITAL_ID,
        name="Valkey Demo Guide",
        price=Decimal("19.99"),
        active=True,
        tags=("guide", "valkey"),
        created_at=datetime.fromisoformat("2026-09-03T12:00:00+00:00"),
        download_url="https://example.com/downloads/valkey-guide.pdf",
        file_size_bytes=5_242_880,
    )


def decode(response: object) -> str:
    assert isinstance(response, bytes)
    return response.decode()


def test_both_product_variants_round_trip() -> None:
    valkey = ValkeyClient()
    try:
        physical = physical_product()
        digital = digital_product()
        valkey.save(physical)
        valkey.save(digital)

        stored_physical = valkey.get(PHYSICAL_ID)
        stored_digital = valkey.get(DIGITAL_ID)
        assert isinstance(stored_physical, PhysicalProduct)
        assert isinstance(stored_digital, DigitalProduct)
        assert stored_physical == physical
        assert stored_digital == digital

        assert valkey.delete(PHYSICAL_ID)
        assert valkey.delete(DIGITAL_ID)
        assert valkey.get(PHYSICAL_ID) is None
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

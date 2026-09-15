"""Unit tests for the Flask product routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from validated_objects.app import create_app
from validated_objects.models import Product


class FakeValkeyClient:
    def __init__(self) -> None:
        self.products: dict[UUID, Product] = {}

    def save(self, product: Product) -> None:
        self.products[product.id] = product

    def get(self, product_id: UUID) -> Product | None:
        return self.products.get(product_id)

    def delete(self, product_id: UUID) -> bool:
        return self.products.pop(product_id, None) is not None


def physical_payload() -> dict[str, Any]:
    return {
        "kind": "physical",
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Mechanical Keyboard",
        "price": "129.90",
        "active": True,
        "tags": ["hardware", "keyboard"],
        "created_at": "2026-09-03T12:00:00Z",
        "stock": 12,
        "weight_grams": 850,
    }


def test_create_read_delete_and_missing_product() -> None:
    valkey: Any = FakeValkeyClient()
    client = create_app(valkey).test_client()
    payload = physical_payload()
    product_id = payload["id"]

    assert client.get("/").get_json() == {
        "application": "validated-object-storage",
        "types": ["physical", "digital"],
    }

    created = client.post("/products", json=payload)
    assert created.status_code == 201
    assert created.get_json()["kind"] == "physical"

    stored = client.get(f"/products/{product_id}")
    assert stored.status_code == 200
    assert stored.get_json() == created.get_json()

    assert client.delete(f"/products/{product_id}").get_json() == {"deleted": True}
    assert client.get(f"/products/{product_id}").status_code == 404


def test_invalid_product_returns_field_errors() -> None:
    valkey: Any = FakeValkeyClient()
    client = create_app(valkey).test_client()
    payload = {**physical_payload(), "stock": -1, "unexpected": True}

    response = client.post("/products", json=payload)

    assert response.status_code == 422
    locations = [error["loc"] for error in response.get_json()["errors"]]
    assert ["physical", "stock"] in locations
    assert ["physical", "unexpected"] in locations
    assert not valkey.products

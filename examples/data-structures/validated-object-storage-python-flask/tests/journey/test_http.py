"""HTTP journey for valid and invalid product variants."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

PHYSICAL_ID = "11111111-1111-4111-8111-111111111111"
DIGITAL_ID = "22222222-2222-4222-8222-222222222222"


def send(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    base_url = os.environ["BASE_URL"]
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def test_valid_variants_and_validation_failure() -> None:
    physical = {
        "kind": "physical",
        "id": PHYSICAL_ID,
        "name": "Mechanical Keyboard",
        "price": "129.90",
        "active": True,
        "tags": ["hardware", "keyboard"],
        "created_at": "2026-09-03T12:00:00Z",
        "stock": 12,
        "weight_grams": 850,
    }
    digital = {
        "kind": "digital",
        "id": DIGITAL_ID,
        "name": "Valkey Demo Guide",
        "price": "19.99",
        "active": True,
        "tags": ["guide", "valkey"],
        "created_at": "2026-09-03T12:00:00Z",
        "download_url": "https://example.com/downloads/valkey-guide.pdf",
        "file_size_bytes": 5_242_880,
    }

    for payload in (physical, digital):
        status, created = send("POST", "/products", payload)
        assert status == 201
        assert created["kind"] == payload["kind"]

        status, stored = send("GET", f"/products/{payload['id']}")
        assert status == 200
        assert stored == created

    invalid = {**physical, "id": "33333333-3333-4333-8333-333333333333", "stock": -1}
    status, body = send("POST", "/products", invalid)
    assert status == 422
    assert body["errors"][0]["loc"] == ["physical", "stock"]

    for product_id in (PHYSICAL_ID, DIGITAL_ID):
        status, body = send("DELETE", f"/products/{product_id}")
        assert status == 200
        assert body == {"deleted": True}

        status, body = send("GET", f"/products/{product_id}")
        assert status == 404
        assert body == {"error": "product not found"}

"""Store two product variants and show one validation failure."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

PHYSICAL_ID = "11111111-1111-4111-8111-111111111111"
DIGITAL_ID = "22222222-2222-4222-8222-222222222222"

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")


def send(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
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
    "file_size_bytes": 5242880,
}
invalid = {**physical, "id": "33333333-3333-4333-8333-333333333333", "stock": -1}

for label, payload in (("physical", physical), ("digital", digital)):
    status, _ = send("POST", "/products", payload)
    print(f"{label} POST -> {status}")
    status, body = send("GET", f"/products/{payload['id']}")
    print(f"{label} GET  -> {status} {body['kind']} product")

status, body = send("POST", "/products", invalid)
print(f"invalid POST  -> {status} {body['errors'][0]['msg']}")

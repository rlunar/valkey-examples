"""HTTP journey against the running Flask application."""

from __future__ import annotations

import json
import os
import urllib.request


def test_store_and_retrieve_value() -> None:
    base_url = os.environ["BASE_URL"]
    expected = f"journey-{os.environ['EXPECTED_TOPOLOGY']}"
    payload = json.dumps({"value": expected}).encode()
    request = urllib.request.Request(
        f"{base_url}/value",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 200
        assert json.load(response) == {"value": expected}

    with urllib.request.urlopen(f"{base_url}/value", timeout=5) as response:
        assert response.status == 200
        assert json.load(response) == {"value": expected}

    delete = urllib.request.Request(f"{base_url}/value", method="DELETE")
    with urllib.request.urlopen(delete, timeout=5) as response:
        assert response.status == 200
        assert json.load(response) == {"deleted": True}

    with urllib.request.urlopen(f"{base_url}/value", timeout=5) as response:
        assert json.load(response) == {"value": None}

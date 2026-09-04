"""Store and retrieve the quickstart value through Flask."""

from __future__ import annotations

import json
import os
import urllib.request

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")
topology = os.environ.get("TOPOLOGY", "standalone")
payload = json.dumps({"value": f"hello from {topology}"}).encode()

request = urllib.request.Request(
    f"{base_url}/value",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=5) as response:
    print(f"POST /value -> {response.read().decode()}")

with urllib.request.urlopen(f"{base_url}/value", timeout=5) as response:
    print(f"GET  /value -> {response.read().decode()}")

"""Delete the two deterministic demo products."""

from __future__ import annotations

import json
import os
import urllib.request

DEMO_IDS = (
    "11111111-1111-4111-8111-111111111111",
    "22222222-2222-4222-8222-222222222222",
)

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")

for product_id in DEMO_IDS:
    request = urllib.request.Request(f"{base_url}/products/{product_id}", method="DELETE")
    with urllib.request.urlopen(request, timeout=5) as response:
        print(json.load(response))

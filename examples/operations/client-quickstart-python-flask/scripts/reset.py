"""Delete the quickstart value through Flask."""

from __future__ import annotations

import os
import urllib.request

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")
request = urllib.request.Request(f"{base_url}/value", method="DELETE")

with urllib.request.urlopen(request, timeout=5) as response:
    print(response.read().decode())

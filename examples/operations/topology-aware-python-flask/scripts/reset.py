#!/usr/bin/env python3
"""Delete only the capsule's known demo counter."""

from __future__ import annotations

import os

import httpx


def main() -> None:
    port = os.getenv("FLASK_PORT", "8000")
    base_url = os.getenv("BASE_URL", f"http://127.0.0.1:{port}")
    response = httpx.delete(f"{base_url}/api/counters/demo", timeout=5)
    response.raise_for_status()
    print("Deleted the demo counter.")


if __name__ == "__main__":
    main()

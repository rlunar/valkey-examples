#!/usr/bin/env python3
"""Wait for an HTTP endpoint without adding curl as a runtime dependency."""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: wait_for_http.py URL TIMEOUT_SECONDS", file=sys.stderr)
        return 2

    url = sys.argv[1]
    deadline = time.monotonic() + float(sys.argv[2])
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return 0
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        time.sleep(0.2)

    print(f"Timed out waiting for {url}: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

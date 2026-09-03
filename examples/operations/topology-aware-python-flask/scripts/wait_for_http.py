#!/usr/bin/env python3
"""Wait until an HTTP endpoint returns a successful status."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    deadline = time.monotonic() + args.timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(args.url, timeout=2) as response:
                if 200 <= response.status < 300:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        time.sleep(0.25)

    raise SystemExit(f"Timed out waiting for {args.url}: {last_error}")


if __name__ == "__main__":
    main()

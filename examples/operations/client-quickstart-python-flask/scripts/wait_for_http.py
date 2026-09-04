"""Wait until an HTTP endpoint returns a successful response."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("--timeout", type=float, default=60)
args = parser.parse_args()

deadline = time.monotonic() + args.timeout
while True:
    try:
        with urllib.request.urlopen(args.url, timeout=2):
            break
    except OSError, urllib.error.URLError:
        if time.monotonic() >= deadline:
            raise SystemExit(f"Timed out waiting for {args.url}") from None
        time.sleep(0.25)

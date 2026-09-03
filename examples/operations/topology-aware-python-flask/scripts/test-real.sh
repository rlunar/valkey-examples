#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

cleanup() {
  docker compose \
    --profile standalone \
    --profile sentinel \
    --profile cluster \
    down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for topology in standalone sentinel cluster; do
  test_port="$(
    uv run --frozen python -c \
      'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
  )"
  base_url="http://127.0.0.1:${test_port}"

  printf '\n== Verify %s topology ==\n' "$topology"
  cleanup

  TOPOLOGY="$topology" FLASK_PORT="$test_port" ./scripts/start.sh

  TOPOLOGY="$topology" FLASK_PORT="$test_port" \
    docker compose --profile "$topology" run \
    --rm \
    --no-deps \
    "app-$topology" \
    pytest tests/integration

  BASE_URL="$base_url" EXPECTED_TOPOLOGY="$topology" \
    uv run --frozen pytest tests/journey

  TOPOLOGY="$topology" FLASK_PORT="$test_port" ./scripts/stop.sh
done

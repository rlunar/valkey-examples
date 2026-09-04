#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

cleanup() {
  docker compose \
    --profile standalone \
    --profile cluster \
    down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for topology in standalone cluster; do
  if [[ "$topology" == "cluster" ]]; then
    addresses="cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379"
  else
    addresses="standalone:6379"
  fi
  message="hello from ${topology}"

  printf '\n== Verify %s ==\n' "$topology"
  cleanup

  TOPOLOGY="$topology" ./scripts/start.sh

  output="$(
    TOPOLOGY="$topology" \
      VALKEY_ADDRESSES="$addresses" \
      VALKEY_MESSAGE="$message" \
      ./scripts/demo.sh
  )"
  printf '%s\n' "$output"
  grep -Fx "$message" <<<"$output" >/dev/null

  TOPOLOGY="$topology" \
    VALKEY_ADDRESSES="$addresses" \
    VALKEY_MESSAGE="$message" \
    docker compose --profile "$topology" run \
      --rm \
      --no-deps \
      -e VALKEY_MODE="$topology" \
      -e VALKEY_ADDRESSES="$addresses" \
      -e VALKEY_MESSAGE="$message" \
      app \
      pytest tests/integration

  TOPOLOGY="$topology" ./scripts/reset.sh
  TOPOLOGY="$topology" ./scripts/stop.sh
done

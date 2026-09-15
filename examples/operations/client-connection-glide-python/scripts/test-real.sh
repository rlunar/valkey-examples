#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

cleanup() {
  compose_all down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for topology in $CAPSULE_TOPOLOGIES; do
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
    compose run \
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

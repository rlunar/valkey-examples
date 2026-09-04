#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if [[ "$TOPOLOGY" == "standalone" ]]; then
  compose up -d --wait standalone
else
  compose up -d --wait cluster-node-1 cluster-node-2 cluster-node-3

  if ! compose exec -T cluster-node-1 \
    valkey-cli cluster info | grep -q '^cluster_state:ok'; then
    compose run --rm --no-deps cluster-init
  fi

  for _ in {1..40}; do
    if compose exec -T cluster-node-1 \
      valkey-cli cluster info | grep -q '^cluster_state:ok'; then
      break
    fi
    sleep 0.25
  done

  compose exec -T cluster-node-1 \
    valkey-cli cluster info | grep -q '^cluster_state:ok'
fi

printf 'Valkey is ready: topology=%s\n' "$TOPOLOGY"

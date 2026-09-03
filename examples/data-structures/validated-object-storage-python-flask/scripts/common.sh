#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"
export TOPOLOGY="${TOPOLOGY:-standalone}"
export FLASK_PORT="${FLASK_PORT:-8000}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:${FLASK_PORT}}"

case "$TOPOLOGY" in
  standalone | cluster)
    ;;
  *)
    printf 'TOPOLOGY must be standalone or cluster; received %s\n' "$TOPOLOGY" >&2
    exit 2
    ;;
esac

app_service() {
  printf 'app-%s\n' "$TOPOLOGY"
}

compose() {
  docker compose --profile "$TOPOLOGY" "$@"
}

compose_all() {
  docker compose --profile standalone --profile cluster "$@"
}

#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

read_dotenv_value() {
  local name="$1"

  [[ -f .env ]] || return 1
  awk -F= -v key="$name" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' .env
}

dotenv_mode="$(read_dotenv_value VALKEY_MODE || true)"
dotenv_addresses="$(read_dotenv_value VALKEY_ADDRESSES || true)"
dotenv_message="$(read_dotenv_value VALKEY_MESSAGE || true)"

export TOPOLOGY="${TOPOLOGY:-${dotenv_mode:-standalone}}"
export VALKEY_ADDRESSES="${VALKEY_ADDRESSES:-${dotenv_addresses:-standalone:6379}}"
export VALKEY_MESSAGE="${VALKEY_MESSAGE:-${dotenv_message:-hello from GLIDE}}"

case "$TOPOLOGY" in
  standalone | cluster)
    ;;
  *)
    printf 'VALKEY_MODE must be standalone or cluster; received %s\n' "$TOPOLOGY" >&2
    exit 2
    ;;
esac

compose() {
  docker compose --profile "$TOPOLOGY" "$@"
}

compose_all() {
  docker compose --profile standalone --profile cluster "$@"
}

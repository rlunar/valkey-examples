#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

read_dotenv_value() {
  local name="$1"
  local line
  local value

  [[ -f .env ]] || return 1
  line="$(awk -F= -v key="$name" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' .env)"
  [[ -n "$line" ]] || return 1
  value="${line%$'\r'}"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s\n' "$value"
}

dotenv_topology="$(read_dotenv_value VALKEY_TOPOLOGY || true)"
dotenv_port="$(read_dotenv_value FLASK_PORT || true)"

export TOPOLOGY="${TOPOLOGY:-${dotenv_topology:-standalone}}"
export FLASK_PORT="${FLASK_PORT:-${dotenv_port:-8000}}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:${FLASK_PORT}}"

case "$TOPOLOGY" in
  standalone | sentinel | cluster)
    ;;
  *)
    printf 'TOPOLOGY must be standalone, sentinel, or cluster; received %s\n' \
      "$TOPOLOGY" >&2
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
  docker compose \
    --profile standalone \
    --profile sentinel \
    --profile cluster \
    "$@"
}

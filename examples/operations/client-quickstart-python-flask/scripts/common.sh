#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export CAPSULE_ID="client-quickstart-python-flask"
export CAPSULE_TOPOLOGIES="standalone cluster"
export CAPSULE_INFRA_PROFILES="valkey-standalone-replicated valkey-cluster-6"

# shellcheck source=../../../infra/scripts/capsule.sh
source "$capsule_root/../../../infra/scripts/capsule.sh"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"
export TOPOLOGY="${TOPOLOGY:-standalone}"
export FLASK_PORT="${FLASK_PORT:-8000}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:${FLASK_PORT}}"

configure_infra_profile() {
  case "$TOPOLOGY" in
    standalone)
      INFRA_PROFILE="valkey-standalone-replicated"
      ;;
    cluster)
      INFRA_PROFILE="valkey-cluster-6"
      ;;
    *)
      printf 'TOPOLOGY must be standalone or cluster; received %s\n' \
        "$TOPOLOGY" >&2
      return 2
      ;;
  esac
  export INFRA_PROFILE
}
configure_infra_profile

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  capsule_command "$@"
fi

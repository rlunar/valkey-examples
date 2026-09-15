#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export CAPSULE_ID="client-connection-glide-python"
export CAPSULE_TOPOLOGIES="standalone cluster"
export CAPSULE_INFRA_PROFILES="valkey-standalone valkey-cluster-3"

# shellcheck source=../../../infra/scripts/capsule.sh
source "$capsule_root/../../../infra/scripts/capsule.sh"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

dotenv_mode="$(read_dotenv_value VALKEY_MODE || true)"
dotenv_addresses="$(read_dotenv_value VALKEY_ADDRESSES || true)"
dotenv_message="$(read_dotenv_value VALKEY_MESSAGE || true)"

export TOPOLOGY="${TOPOLOGY:-${dotenv_mode:-standalone}}"
export VALKEY_ADDRESSES="${VALKEY_ADDRESSES:-${dotenv_addresses:-standalone:6379}}"
export VALKEY_MESSAGE="${VALKEY_MESSAGE:-${dotenv_message:-hello from GLIDE}}"

configure_infra_profile() {
  case "$TOPOLOGY" in
    standalone)
      INFRA_PROFILE="valkey-standalone"
      ;;
    cluster)
      INFRA_PROFILE="valkey-cluster-3"
      ;;
    *)
      printf 'VALKEY_MODE must be standalone or cluster; received %s\n' \
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

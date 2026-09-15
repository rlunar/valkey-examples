#!/usr/bin/env bash

set -euo pipefail

# This script adds one topology-specific proof after the shared PING, SET, GET,
# and INFO checks in validate-valkey.sh.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$script_dir/.." && pwd)"
deployment="${1:-}"

usage() {
  printf 'Usage: %s standalone|sentinel|cluster\n' "${0##*/}" >&2
}

compose() {
  local profile="$1"
  shift

  docker compose \
    --project-directory "$infra_root" \
    -f "$infra_root/compose.yaml" \
    --profile "$profile" \
    "$@"
}

require_running_service() {
  local profile="$1"
  local service="$2"

  if [[ "$(compose "$profile" ps --status running --services "$service")" != "$service" ]]; then
    printf 'Required service is not running: %s\n' "$service" >&2
    printf 'Start it with: make start PROFILE=%s\n' "$profile" >&2
    exit 2
  fi
}

demo_standalone() {
  printf 'Deployment: standalone\n'
  "$infra_root/scripts/validate-valkey.sh" standalone
}

sentinel_primary() {
  compose valkey-sentinel exec -T sentinel-1 \
    valkey-cli --raw -p 26379 \
    SENTINEL get-master-addr-by-name demo-primary
}

demo_sentinel() {
  local profile="valkey-sentinel"
  local key="valkey-examples:infra:sentinel"
  local initial_address
  local initial_primary
  local initial_port
  local promoted_address
  local promoted_primary=""
  local promoted_port=""
  local promoted_role=""
  local replicas_acknowledged
  local value

  require_running_service "$profile" sentinel-primary
  require_running_service "$profile" sentinel-replica
  require_running_service "$profile" sentinel-1

  printf 'Deployment: sentinel\n'

  # 1. Ask Sentinel which node is the primary before the failure.
  initial_address="$(sentinel_primary)"
  initial_primary="$(printf '%s\n' "$initial_address" | sed -n '1p')"
  initial_port="$(printf '%s\n' "$initial_address" | sed -n '2p')"
  if [[ -z "$initial_primary" || -z "$initial_port" ]]; then
    printf 'Sentinel did not report an initial primary.\n' >&2
    exit 1
  fi

  # 2. Write a value and wait until the replica confirms it has the copy.
  "$infra_root/scripts/validate-valkey.sh" sentinel
  replicas_acknowledged="$(
    compose "$profile" exec -T sentinel-primary \
      valkey-cli --raw WAIT 1 5000
  )"
  if [[ "$replicas_acknowledged" != "1" ]]; then
    printf 'Replica did not acknowledge the demo write.\n' >&2
    exit 1
  fi

  printf 'Initial primary: %s:%s\n' "$initial_primary" "$initial_port"
  printf 'Replicas acknowledged: %s\n' "$replicas_acknowledged"
  # 3. Stop the primary so Sentinel must promote the replica.
  printf 'Stopping sentinel-primary to trigger failover.\n'
  compose "$profile" stop sentinel-primary >/dev/null

  # 4. Poll until Sentinel reports a different primary and the replica agrees.
  for _attempt in {1..30}; do
    promoted_address="$(sentinel_primary)"
    promoted_primary="$(printf '%s\n' "$promoted_address" | sed -n '1p')"
    promoted_port="$(printf '%s\n' "$promoted_address" | sed -n '2p')"
    promoted_role="$(
      compose "$profile" exec -T sentinel-replica \
        valkey-cli --raw INFO replication |
        awk -F: '$1 == "role" { sub(/\r$/, "", $2); print $2; exit }'
    )"
    if [[ "$promoted_primary" != "$initial_primary" &&
      "$promoted_port" == "6379" &&
      "$promoted_role" == "master" ]]; then
      break
    fi
    sleep 1
  done

  if [[ "$promoted_primary" == "$initial_primary" ||
    "$promoted_port" != "6379" ||
    "$promoted_role" != "master" ]]; then
    printf 'Sentinel did not promote the replica within 30 seconds.\n' >&2
    exit 1
  fi

  # 5. Read the original value from the promoted replica.
  value="$(
    compose "$profile" exec -T sentinel-replica \
      valkey-cli --raw GET "$key"
  )"

  printf 'Promoted primary: sentinel-replica:%s\n' "$promoted_port"
  printf 'Promoted INFO replication:\nrole:%s\n' "$promoted_role"
  printf 'GET after failover: %s\n' "$value"
}

demo_cluster() {
  local profile="valkey-cluster-3"
  local cluster_state
  local slots_assigned
  local primary_nodes

  require_running_service "$profile" cluster-node-1
  require_running_service "$profile" cluster-node-2
  require_running_service "$profile" cluster-node-3

  # Wait until the nodes agree that the cluster is ready.
  for _attempt in {1..30}; do
    cluster_state="$(
      compose "$profile" exec -T cluster-node-1 \
        valkey-cli --raw CLUSTER INFO |
        awk -F: '$1 == "cluster_state" { sub(/\r$/, "", $2); print $2; exit }'
    )"
    if [[ "$cluster_state" == "ok" ]]; then
      break
    fi
    sleep 1
  done

  if [[ "$cluster_state" != "ok" ]]; then
    printf 'Valkey Cluster did not become ready within 30 seconds.\n' >&2
    exit 1
  fi

  printf 'Deployment: cluster\n'
  "$infra_root/scripts/validate-valkey.sh" cluster

  slots_assigned="$(
    compose "$profile" exec -T cluster-node-1 \
      valkey-cli --raw CLUSTER INFO |
      awk -F: '$1 == "cluster_slots_assigned" { sub(/\r$/, "", $2); print $2; exit }'
  )"
  primary_nodes="$(
    compose "$profile" exec -T cluster-node-1 \
      valkey-cli --raw CLUSTER NODES |
      awk '$3 ~ /(^|,)master(,|$)/ && $3 !~ /fail/ { count += 1 } END { print count + 0 }'
  )"
  printf 'Cluster state: %s\n' "$cluster_state"
  printf 'Slots assigned: %s\n' "$slots_assigned"
  printf 'Primary nodes: %s\n' "$primary_nodes"
}

case "$deployment" in
  standalone)
    demo_standalone
    ;;
  sentinel)
    demo_sentinel
    ;;
  cluster)
    demo_cluster
    ;;
  *)
    usage
    exit 2
    ;;
esac

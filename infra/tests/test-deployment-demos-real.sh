#!/usr/bin/env bash

set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$test_dir/.." && pwd)"
project_name="valkey-example-deployment-demos-$$"
all_profiles=(
  valkey-standalone
  valkey-sentinel
  valkey-cluster-3
)

compose() {
  local profile="$1"
  shift

  COMPOSE_PROJECT_NAME="$project_name" \
    CAPSULE_ID="deployment-demos" \
    INFRA_ROOT="$infra_root" \
    docker compose \
    --project-directory "$infra_root" \
    -f "$infra_root/compose.yaml" \
    --profile "$profile" \
    "$@"
}

compose_all() {
  local profile
  local profile_args=()

  for profile in "${all_profiles[@]}"; do
    profile_args+=(--profile "$profile")
  done

  COMPOSE_PROJECT_NAME="$project_name" \
    CAPSULE_ID="deployment-demos" \
    INFRA_ROOT="$infra_root" \
    docker compose \
    --project-directory "$infra_root" \
    -f "$infra_root/compose.yaml" \
    "${profile_args[@]}" \
    "$@"
}

demo() {
  local deployment="$1"

  COMPOSE_PROJECT_NAME="$project_name" \
    CAPSULE_ID="deployment-demos" \
    INFRA_ROOT="$infra_root" \
    "$infra_root/scripts/demo-deployment.sh" "$deployment"
}

cleanup() {
  compose_all down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

cleanup
compose valkey-standalone up -d --wait
standalone_output="$(demo standalone)"
grep -q '^Container: standalone (running)$' <<<"$standalone_output"
grep -q '^PING: PONG$' <<<"$standalone_output"
grep -q '^SET: OK$' <<<"$standalone_output"
grep -q '^GET: standalone-demo$' <<<"$standalone_output"
grep -q '^INFO server:$' <<<"$standalone_output"
grep -q '^server_mode:standalone$' <<<"$standalone_output"
grep -q '^INFO memory:$' <<<"$standalone_output"
grep -q '^maxmemory_policy:noeviction$' <<<"$standalone_output"
grep -q '^INFO replication:$' <<<"$standalone_output"
grep -q '^role:master$' <<<"$standalone_output"

cleanup
compose valkey-sentinel up -d --wait
sentinel_output="$(demo sentinel)"
grep -q '^Initial primary: sentinel-primary:6379$' <<<"$sentinel_output"
grep -q '^Container: sentinel-primary (running)$' <<<"$sentinel_output"
grep -q '^PING: PONG$' <<<"$sentinel_output"
grep -q '^SET: OK$' <<<"$sentinel_output"
grep -q '^GET: before-failover$' <<<"$sentinel_output"
grep -q '^server_mode:standalone$' <<<"$sentinel_output"
grep -q '^maxmemory_policy:noeviction$' <<<"$sentinel_output"
grep -q '^INFO replication:$' <<<"$sentinel_output"
grep -q '^Promoted primary: sentinel-replica:6379$' <<<"$sentinel_output"
grep -q '^Promoted INFO replication:$' <<<"$sentinel_output"
grep -q '^GET after failover: before-failover$' <<<"$sentinel_output"

cleanup
compose valkey-cluster-3 up -d --wait
cluster_output="$(demo cluster)"
grep -q '^Cluster state: ok$' <<<"$cluster_output"
grep -q '^Container: cluster-node-1 (running)$' <<<"$cluster_output"
grep -q '^PING: PONG$' <<<"$cluster_output"
grep -q '^SET: OK$' <<<"$cluster_output"
grep -q '^GET: cluster-demo$' <<<"$cluster_output"
grep -q '^INFO server:$' <<<"$cluster_output"
grep -q '^server_mode:cluster$' <<<"$cluster_output"
grep -q '^INFO memory:$' <<<"$cluster_output"
grep -q '^maxmemory_policy:noeviction$' <<<"$cluster_output"
grep -q '^INFO replication:$' <<<"$cluster_output"
grep -q '^Slots assigned: 16384$' <<<"$cluster_output"
grep -q '^Primary nodes: 3$' <<<"$cluster_output"

printf 'Standalone, Sentinel, and cluster demos are valid.\n'

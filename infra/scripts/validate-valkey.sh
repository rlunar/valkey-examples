#!/usr/bin/env bash

set -euo pipefail

# Every validation mode follows the same student-visible path:
# container running -> PING -> SET -> GET -> selected INFO fields.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$script_dir/.." && pwd)"
validation="${1:-}"

usage() {
  printf 'Usage: %s plaintext|tls|standalone|sentinel|cluster\n' "${0##*/}" >&2
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

profile=""
service=""
display_name=""
transport="plaintext"
key=""
expected_value=""
cli_args=(-h 127.0.0.1 -p 6379)

case "$validation" in
  plaintext)
    profile="valkey-standalone-host"
    service="valkey"
    display_name="plaintext host profile"
    key="valkey-examples:infra:plaintext"
    expected_value="plaintext-demo"
    ;;
  tls)
    profile="valkey-standalone-tls-host"
    service="valkey-tls"
    display_name="mutual TLS host profile"
    transport="mutual TLS"
    key="valkey-examples:infra:tls"
    expected_value="tls-demo"
    cli_args=(
      --tls
      --cacert /tls/ca.crt
      --cert /tls/client.crt
      --key /tls/client.key
      -h 127.0.0.1
      -p 6379
    )
    ;;
  standalone)
    profile="valkey-standalone"
    service="standalone"
    display_name="standalone topology"
    key="valkey-examples:infra:standalone"
    expected_value="standalone-demo"
    ;;
  sentinel)
    profile="valkey-sentinel"
    service="sentinel-primary"
    display_name="Sentinel primary"
    key="valkey-examples:infra:sentinel"
    expected_value="before-failover"
    ;;
  cluster)
    profile="valkey-cluster-3"
    service="cluster-node-1"
    display_name="cluster bootstrap node"
    key="valkey-examples:infra:cluster:{demo}"
    expected_value="cluster-demo"
    cli_args=(-c -h 127.0.0.1 -p 6379)
    ;;
  *)
    usage
    exit 2
    ;;
esac

if [[ "$(compose "$profile" ps --status running --services "$service")" != "$service" ]]; then
  printf 'Required container is not running: %s\n' "$service" >&2
  printf 'Start it with: make start PROFILE=%s\n' "$profile" >&2
  exit 2
fi

valkey_cli() {
  compose "$profile" exec -T "$service" \
    valkey-cli "${cli_args[@]}" "$@"
}

ping_result="$(valkey_cli ping)"
set_result="$(valkey_cli SET "$key" "$expected_value")"
get_result="$(valkey_cli --raw GET "$key")"

# INFO returns many lines. Keep only the fields used by the tutorials.
server_info="$(valkey_cli --raw INFO server | tr -d '\r')"
memory_info="$(valkey_cli --raw INFO memory | tr -d '\r')"
replication_info="$(valkey_cli --raw INFO replication | tr -d '\r')"

if [[ "$ping_result" != "PONG" ]]; then
  printf 'PING failed for %s: %s\n' "$service" "$ping_result" >&2
  exit 1
fi
if [[ "$set_result" != "OK" || "$get_result" != "$expected_value" ]]; then
  printf 'SET/GET round trip failed for %s.\n' "$service" >&2
  exit 1
fi

server_fields="$(
  printf '%s\n' "$server_info" |
    awk -F: '
      $1 == "valkey_version" ||
      $1 == "server_mode" ||
      $1 == "tcp_port" {
        print
      }
    '
)"
memory_fields="$(
  printf '%s\n' "$memory_info" |
    awk -F: '
      $1 == "maxmemory" ||
      $1 == "maxmemory_policy" {
        print
      }
    '
)"
replication_fields="$(
  printf '%s\n' "$replication_info" |
    awk -F: '$1 == "role" { print }'
)"

if [[ -z "$server_fields" || -z "$memory_fields" || -z "$replication_fields" ]]; then
  printf 'INFO did not return the required server, memory, and replication fields.\n' >&2
  exit 1
fi

printf 'Validation: %s\n' "$display_name"
printf 'Container: %s (running)\n' "$service"
printf 'Transport: %s\n' "$transport"
printf 'PING: %s\n' "$ping_result"
printf 'Key: %s\n' "$key"
printf 'SET: %s\n' "$set_result"
printf 'GET: %s\n' "$get_result"
printf 'INFO server:\n%s\n' "$server_fields"
printf 'INFO memory:\n%s\n' "$memory_fields"
printf 'INFO replication:\n%s\n' "$replication_fields"

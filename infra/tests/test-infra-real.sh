#!/usr/bin/env bash

set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$test_dir/.." && pwd)"
project_name="valkey-example-infra-smoke-$$"
tls_dir="${TLS_CERT_DIR:-$infra_root/.cache/tls}"

free_port() {
  python3 -c \
    'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
}

plain_port="$(free_port)"
tls_port="$(free_port)"

compose() {
  COMPOSE_PROJECT_NAME="$project_name" \
    CAPSULE_ID="infra-smoke" \
    INFRA_ROOT="$infra_root" \
    TLS_CERT_DIR="$tls_dir" \
    VALKEY_PORT="$plain_port" \
    VALKEY_TLS_PORT="$tls_port" \
    docker compose \
    --project-directory "$infra_root" \
    -f "$infra_root/compose.yaml" \
    --profile valkey-standalone-host \
    --profile valkey-standalone-tls-host \
    "$@"
}

cleanup() {
  compose down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

"$infra_root/scripts/generate-tls-certs.sh" "$tls_dir"
cleanup
compose up -d --wait valkey valkey-tls

plain_value() {
  local setting="$1"
  compose exec -T valkey valkey-cli --raw CONFIG GET "$setting" | tail -1
}

validate() {
  local validation="$1"

  COMPOSE_PROJECT_NAME="$project_name" \
    CAPSULE_ID="infra-smoke" \
    INFRA_ROOT="$infra_root" \
    TLS_CERT_DIR="$tls_dir" \
    VALKEY_PORT="$plain_port" \
    VALKEY_TLS_PORT="$tls_port" \
    "$infra_root/scripts/validate-valkey.sh" "$validation"
}

[[ "$(plain_value io-threads)" == "2" ]]
[[ "$(plain_value maxmemory)" == "268435456" ]]
[[ "$(plain_value maxmemory-policy)" == "noeviction" ]]
[[ "$(plain_value maxmemory-samples)" == "5" ]]

plaintext_output="$(validate plaintext)"
grep -q '^Container: valkey (running)$' <<<"$plaintext_output"
grep -q '^Transport: plaintext$' <<<"$plaintext_output"
grep -q '^PING: PONG$' <<<"$plaintext_output"
grep -q '^SET: OK$' <<<"$plaintext_output"
grep -q '^GET: plaintext-demo$' <<<"$plaintext_output"
grep -q '^INFO server:$' <<<"$plaintext_output"
grep -q '^valkey_version:9.1.1$' <<<"$plaintext_output"
grep -q '^server_mode:standalone$' <<<"$plaintext_output"
grep -q '^tcp_port:6379$' <<<"$plaintext_output"
grep -q '^INFO memory:$' <<<"$plaintext_output"
grep -q '^maxmemory:268435456$' <<<"$plaintext_output"
grep -q '^maxmemory_policy:noeviction$' <<<"$plaintext_output"
grep -q '^INFO replication:$' <<<"$plaintext_output"
grep -q '^role:master$' <<<"$plaintext_output"

tls_output="$(validate tls)"
grep -q '^Container: valkey-tls (running)$' <<<"$tls_output"
grep -q '^Transport: mutual TLS$' <<<"$tls_output"
grep -q '^PING: PONG$' <<<"$tls_output"
grep -q '^SET: OK$' <<<"$tls_output"
grep -q '^GET: tls-demo$' <<<"$tls_output"
grep -q '^INFO server:$' <<<"$tls_output"
grep -q '^valkey_version:9.1.1$' <<<"$tls_output"
grep -q '^server_mode:standalone$' <<<"$tls_output"
grep -q '^tcp_port:6379$' <<<"$tls_output"
grep -q '^INFO memory:$' <<<"$tls_output"
grep -q '^maxmemory:268435456$' <<<"$tls_output"
grep -q '^maxmemory_policy:noeviction$' <<<"$tls_output"
grep -q '^INFO replication:$' <<<"$tls_output"
grep -q '^role:master$' <<<"$tls_output"

if compose exec -T valkey-tls valkey-cli \
  --tls \
  --cacert /tls/ca.crt \
  -h 127.0.0.1 \
  -p 6379 \
  ping >/dev/null 2>&1; then
  printf 'TLS accepted a client without the required client certificate.\n' >&2
  exit 1
fi

openssl s_client \
  -connect "127.0.0.1:${tls_port}" \
  -CAfile "$tls_dir/ca.crt" \
  -cert "$tls_dir/client.crt" \
  -key "$tls_dir/client.key" \
  -verify_ip 127.0.0.1 \
  -verify_return_error \
  -brief </dev/null >/dev/null 2>&1

printf 'Plaintext and mutual-TLS validation, tuning, and authentication are valid.\n'

#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/common.sh"

response="$(
  printf 'HTTP/1.1 429 Too Many Requests\r\n'
  printf 'Content-Type: application/json\r\n'
  printf 'Retry-After: 10\r\n'
  printf '\r\n'
  printf '{"allowed":false}\n'
)"

status="$(http_status_from_response <<<"$response")"
retry_after="$(retry_after_from_response <<<"$response")"

[[ "$status" == "429" ]]
[[ "$retry_after" == "10" ]]
[[ "$(CI=1 request_outcome 200 "accepted request")" == "✅ 200 Accepted — accepted request" ]]
[[ "$(CI=1 request_outcome 429 "denied request")" == "❌ 429 Denied — denied request" ]]
key_state="$(printf 'hashed-key\n5\n' | format_key_state)"
[[ "$key_state" == $'🔑 hashed-key\n   members: 5' ]]

test_runtime="$(mktemp -d)"
export RUNTIME_DIR="$test_runtime"
export DEMO_LOCK_DIR="$RUNTIME_DIR/demo.lock"
cleanup() {
  release_demo_lock
  rm -f "$test_runtime/test.env"
  rmdir "$test_runtime" 2>/dev/null || true
}
trap cleanup EXIT

printf 'RATE_LIMIT_REQUESTS=7\n' >"$test_runtime/test.env"
RATE_LIMIT_REQUESTS=9
export RATE_LIMIT_REQUESTS
load_dotenv_defaults "$test_runtime/test.env"
[[ "$RATE_LIMIT_REQUESTS" == "9" ]]
unset RATE_LIMIT_REQUESTS
load_dotenv_defaults "$test_runtime/test.env"
[[ "$RATE_LIMIT_REQUESTS" == "7" ]]

acquire_demo_lock
if acquire_demo_lock 2>/dev/null; then
  printf 'A second demo lock was acquired unexpectedly.\n' >&2
  exit 1
fi

printf 'Demo response parsing is valid.\n'

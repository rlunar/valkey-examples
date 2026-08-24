#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

acquire_demo_lock

cleanup() {
  make stop >/dev/null 2>&1 || true
  release_demo_lock
}
trap cleanup EXIT INT TERM

heading "Check prerequisites"
./scripts/doctor.sh

heading "Install the locked Python environment"
if [[ "${CI:-0}" != "1" ]] && command -v gum >/dev/null; then
  gum spin --spinner dot --title "uv sync --frozen" -- make setup
else
  make setup
fi

heading "Start Valkey and Flask"
make start
make reset
printf 'Selected implementation: %s\n' "$RATE_LIMIT_IMPLEMENTATION"
printf 'Policy: %s requests per %s ms\n' "$RATE_LIMIT_REQUESTS" "$RATE_LIMIT_WINDOW_MS"

heading "Implementation source"
implementation_file="src/rate_limiter_demo/valkey/multi_exec.py"
if [[ "$RATE_LIMIT_IMPLEMENTATION" == "lua" ]]; then
  implementation_file="src/rate_limiter_demo/valkey/scripts/sliding_window.lua"
fi
if command -v bat >/dev/null && [[ "${CI:-0}" != "1" ]]; then
  bat --style=plain --paging=never "$implementation_file"
else
  sed -n '1,220p' "$implementation_file"
fi

if command -v yq >/dev/null; then
  heading "Capsule manifest"
  yq '.id, .status, .valkey.image, .clients' example.yaml
fi

client_a="demo-user-a"
client_b="demo-user-b"
base_url="http://${FLASK_HOST}:${FLASK_PORT}"
pretty="all"
if [[ "${CI:-0}" == "1" ]]; then
  pretty="none"
fi

last_response=""
last_status=""
send_request() {
  local identity="$1"
  local expected_statuses="$2"
  local label="$3"
  local response_file
  local plain_file
  local status

  response_file="$(mktemp)"
  plain_file="$(mktemp)"
  http --pretty="$pretty" --print=hb GET \
    "${base_url}/api/limited" "X-Client-ID:${identity}" | tee "$response_file"
  sed $'s/\033\\[[0-9;]*[mK]//g' "$response_file" >"$plain_file"
  status="$(http_status_from_response <"$plain_file")"

  case ",${expected_statuses}," in
    *",${status},"*) ;;
    *)
      printf '%s: expected HTTP %s, got %s\n' \
        "$label" "$expected_statuses" "$status" >&2
      rm -f "$response_file" "$plain_file"
      exit 1
      ;;
  esac

  rm -f "$last_response"
  last_response="$plain_file"
  last_status="$status"
  rm -f "$response_file"
  request_outcome "$status" "$label"
}

heading "Identity A consumes its rolling-window budget"
for request_number in $(seq 1 "$RATE_LIMIT_REQUESTS"); do
  send_request "$client_a" 200 "identity A request ${request_number}"
done

heading "Identity A is denied"
send_request "$client_a" 429 "identity A over limit"
retry_after="$(retry_after_from_response <"$last_response")"
if [[ -z "$retry_after" ]] || ! [[ "$retry_after" =~ ^[0-9]+$ ]]; then
  printf 'The 429 response did not contain a valid Retry-After header.\n' >&2
  exit 1
fi

heading "Identity B has an independent budget"
send_request "$client_b" 200 "identity B first request"

heading "Bounded Valkey state"
compose exec -T valkey valkey-cli --raw EVAL \
  "local c='0'; local out={}; repeat local r=redis.call('SCAN',c,'MATCH',ARGV[1],'COUNT',100); c=r[1]; for _,k in ipairs(r[2]) do table.insert(out,k); table.insert(out,redis.call('ZCARD',k)); end; until c=='0'; return out" \
  0 "${RATE_LIMIT_KEY_PREFIX}:*" | format_key_state

heading "Identity A is allowed after the rolling window advances"
window_seconds=$(((RATE_LIMIT_WINDOW_MS + 999) / 1000))
recovery_deadline=$(($(date +%s) + (window_seconds * 2) + 5))
recovery_attempt=0
recovered=0

while ((recovery_attempt < 5)); do
  recovery_attempt=$((recovery_attempt + 1))
  if (($(date +%s) + retry_after > recovery_deadline)); then
    printf 'Recovery would exceed the bounded demo deadline.\n' >&2
    break
  fi

  printf 'Waiting for Retry-After: %s second(s), attempt %s of 5\n' \
    "$retry_after" "$recovery_attempt"
  sleep "$retry_after"
  send_request "$client_a" "200,429" "identity A recovery attempt ${recovery_attempt}"

  if [[ "$last_status" == "200" ]]; then
    recovered=1
    break
  fi

  retry_after="$(retry_after_from_response <"$last_response")"
  if [[ -z "$retry_after" ]] || ! [[ "$retry_after" =~ ^[0-9]+$ ]]; then
    printf 'A recovery 429 did not contain a valid Retry-After header.\n' >&2
    exit 1
  fi
done

if ((recovered == 0)); then
  printf 'Identity A was not admitted within the bounded recovery loop.\n' >&2
  exit 1
fi

rm -f "$last_response"
heading "Demo complete"
printf 'Both identities were isolated and all expected HTTP statuses were observed.\n'

#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

load_dotenv_defaults() {
  local dotenv_file="$1"
  local line
  local name
  local value

  [[ -f "$dotenv_file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line#export }"
    [[ "$line" == *=* ]] || continue
    name="${line%%=*}"
    value="${line#*=}"

    case "$name" in
      RATE_LIMIT_IMPLEMENTATION | RATE_LIMIT_REQUESTS | RATE_LIMIT_WINDOW_MS | \
        RATE_LIMIT_POLICY_ID | RATE_LIMIT_KEY_PREFIX | RATE_LIMIT_MAX_RETRIES | \
        VALKEY_HOST | VALKEY_PORT | VALKEY_REQUEST_TIMEOUT_MS | FLASK_HOST | FLASK_PORT)
        ;;
      *)
        continue
        ;;
    esac

    if [[ -z "${!name+x}" ]]; then
      if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
      fi
      printf -v "$name" '%s' "$value"
      export "${name?}"
    fi
  done <"$dotenv_file"
}

load_dotenv_defaults .env

export RATE_LIMIT_IMPLEMENTATION="${RATE_LIMIT_IMPLEMENTATION:-multi-exec}"
export RATE_LIMIT_REQUESTS="${RATE_LIMIT_REQUESTS:-5}"
export RATE_LIMIT_WINDOW_MS="${RATE_LIMIT_WINDOW_MS:-10000}"
export RATE_LIMIT_POLICY_ID="${RATE_LIMIT_POLICY_ID:-default}"
export RATE_LIMIT_KEY_PREFIX="${RATE_LIMIT_KEY_PREFIX:-valkey-examples:rate-limit:v1}"
export RATE_LIMIT_MAX_RETRIES="${RATE_LIMIT_MAX_RETRIES:-50}"
export VALKEY_HOST="${VALKEY_HOST:-127.0.0.1}"
export VALKEY_PORT="${VALKEY_PORT:-6379}"
export VALKEY_REQUEST_TIMEOUT_MS="${VALKEY_REQUEST_TIMEOUT_MS:-1000}"
export FLASK_HOST="${FLASK_HOST:-127.0.0.1}"
export FLASK_PORT="${FLASK_PORT:-8000}"

export RUNTIME_DIR="$capsule_root/.runtime"
export PID_FILE="$RUNTIME_DIR/flask.pid"
export LOG_FILE="$RUNTIME_DIR/flask.log"
export DEMO_LOCK_DIR="$RUNTIME_DIR/demo.lock"

compose() {
  docker compose "$@"
}

plain_heading() {
  printf '\n== %s ==\n' "$1"
}

heading() {
  if [[ "${CI:-0}" != "1" ]] && command -v gum >/dev/null; then
    gum style --bold --foreground 212 --margin "1 0 0" "$1"
  else
    plain_heading "$1"
  fi
}

http_status_from_response() {
  awk '/^HTTP\// { print $2; exit }'
}

retry_after_from_response() {
  awk -F': *' '
    tolower($1) == "retry-after" {
      sub(/\r$/, "", $2)
      print $2
      exit
    }
  '
}

request_outcome() {
  local status="$1"
  local label="$2"
  local color
  local message

  case "$status" in
    200)
      color="2"
      message="✅ 200 Accepted — ${label}"
      ;;
    429)
      color="1"
      message="❌ 429 Denied — ${label}"
      ;;
    *)
      color="3"
      message="⚠️ ${status} Unexpected — ${label}"
      ;;
  esac

  if [[ "${CI:-0}" != "1" ]] && command -v gum >/dev/null; then
    gum style --bold --foreground "$color" "$message"
  else
    printf '%s\n' "$message"
  fi
}

format_key_state() {
  awk '
    NR % 2 == 1 { print "🔑 " $0 }
    NR % 2 == 0 { print "   members: " $0 }
  '
}

is_owned_flask_process() {
  local process_id="$1"
  local process_command

  [[ "$process_id" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$process_id" 2>/dev/null || return 1
  process_command="$(ps -p "$process_id" -o command= 2>/dev/null || true)"
  [[ "$process_command" == *"$capsule_root"* ]] &&
    [[ "$process_command" == *"rate-limiter-demo"* ]]
}

acquire_demo_lock() {
  local owner_pid=""

  mkdir -p "$RUNTIME_DIR"
  if mkdir "$DEMO_LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" >"$DEMO_LOCK_DIR/pid"
    return 0
  fi

  if [[ -f "$DEMO_LOCK_DIR/pid" ]]; then
    owner_pid="$(cat "$DEMO_LOCK_DIR/pid")"
  fi
  if [[ "$owner_pid" =~ ^[0-9]+$ ]] && kill -0 "$owner_pid" 2>/dev/null; then
    printf 'Another make demo is already running with PID %s.\n' "$owner_pid" >&2
    return 1
  fi

  rm -f "$DEMO_LOCK_DIR/pid"
  rmdir "$DEMO_LOCK_DIR"
  mkdir "$DEMO_LOCK_DIR"
  printf '%s\n' "$$" >"$DEMO_LOCK_DIR/pid"
}

release_demo_lock() {
  rm -f "$DEMO_LOCK_DIR/pid"
  rmdir "$DEMO_LOCK_DIR" 2>/dev/null || true
}

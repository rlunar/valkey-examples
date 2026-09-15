#!/usr/bin/env bash

if [[ -n "${VALKEY_EXAMPLES_RATE_LIMITER_SH_LOADED:-}" ]]; then
  return 0
fi
readonly VALKEY_EXAMPLES_RATE_LIMITER_SH_LOADED=1

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

acquire_demo_lock() {
  local owner_pid=""

  mkdir -p "$RUNTIME_DIR"
  if mkdir "$DEMO_LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" >"$DEMO_LOCK_DIR/pid"
    return 0
  fi

  if [[ -f "$DEMO_LOCK_DIR/pid" ]]; then
    owner_pid="$(<"$DEMO_LOCK_DIR/pid")"
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

rate_limiter_doctor() {
  local missing=0
  local command_name
  local optional_missing=()

  for command_name in make docker uv http; do
    if ! command -v "$command_name" >/dev/null; then
      printf 'Missing required command: %s\n' "$command_name" >&2
      missing=1
    fi
  done

  if ((missing)); then
    printf '\nInstall uv and HTTPie with Homebrew on macOS:\n  brew bundle\n' >&2
    printf 'Docker Desktop or another Docker Engine with Compose v2 must also be running.\n' >&2
    return 1
  fi

  docker compose version >/dev/null
  docker info >/dev/null

  printf 'uv:      %s\n' "$(uv --version)"
  printf 'python:  %s\n' "$(uv python find 3.14)"
  printf 'docker:  %s\n' "$(docker --version)"
  printf 'compose: %s\n' "$(docker compose version --short)"
  printf 'httpie:  %s\n' "$(http --version | head -1)"

  for command_name in gum bat jq yq vhs shellcheck; do
    if ! command -v "$command_name" >/dev/null; then
      optional_missing+=("$command_name")
    fi
  done

  if ((${#optional_missing[@]})); then
    printf 'Optional presentation tools not found: %s (run brew bundle)\n' \
      "${optional_missing[*]}"
  fi
}

rate_limiter_reset() {
  local pattern="${RATE_LIMIT_KEY_PREFIX}:*"
  local deleted

  deleted="$(
    compose exec -T valkey valkey-cli --raw EVAL \
      "local c='0'; local n=0; repeat local r=redis.call('SCAN',c,'MATCH',ARGV[1],'COUNT',100); c=r[1]; for _,k in ipairs(r[2]) do n=n+redis.call('DEL',k); end; until c=='0'; return n" \
      0 "$pattern"
  )"
  printf 'Deleted %s rate-limit key(s) matching %s\n' "$deleted" "$pattern"
}

rate_limiter_test_real() {
  # shellcheck disable=SC2329
  cleanup_rate_limiter() {
    compose down --remove-orphans
  }
  trap cleanup_rate_limiter EXIT INT TERM

  compose up -d --wait valkey
  uv run --frozen pytest tests --cov --cov-report=term-missing
}

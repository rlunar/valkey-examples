#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

mkdir -p "$RUNTIME_DIR"

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE")"
  if is_owned_app_process "$existing_pid"; then
    if ! uv run --frozen python scripts/wait_for_http.py \
      "http://${APP_HOST}:${APP_PORT}/health/ready" 3; then
      printf 'Recorded app process %s is not healthy; run make stop first.\n' \
        "$existing_pid" >&2
      exit 1
    fi
    printf 'FastAPI app is already running with PID %s\n' "$existing_pid"
    exit 0
  fi
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
    printf 'Ignoring stale PID file: process %s is not owned by this capsule.\n' \
      "$existing_pid" >&2
  fi
  rm -f "$PID_FILE"
fi

compose up -d --wait valkey

uv run --frozen rate-limiter-demo >"$LOG_FILE" 2>&1 &
app_pid=$!
printf '%s\n' "$app_pid" >"$PID_FILE"

cleanup_failed_start() {
  kill "$app_pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  printf 'FastAPI app failed to become ready. Log output:\n' >&2
  tail -50 "$LOG_FILE" >&2 || true
}

if ! uv run --frozen python scripts/wait_for_http.py \
  "http://${APP_HOST}:${APP_PORT}/health/ready" 30; then
  cleanup_failed_start
  exit 1
fi

printf 'Valkey and FastAPI are ready (implementation=%s, PID=%s).\n' \
  "$RATE_LIMIT_IMPLEMENTATION" "$app_pid"

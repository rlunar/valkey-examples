#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if [[ -f "$PID_FILE" ]]; then
  app_pid="$(cat "$PID_FILE")"
  if is_owned_flask_process "$app_pid"; then
    kill "$app_pid"
    for _attempt in {1..50}; do
      if ! kill -0 "$app_pid" 2>/dev/null; then
        break
      fi
      sleep 0.1
    done
  elif [[ "$app_pid" =~ ^[0-9]+$ ]] && kill -0 "$app_pid" 2>/dev/null; then
    printf 'Did not stop PID %s because it is not owned by this capsule.\n' \
      "$app_pid" >&2
  fi
  rm -f "$PID_FILE"
fi

compose down --remove-orphans
printf 'Stopped resources owned by sliding-window-python-flask.\n'

#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if ! compose up -d --build --wait "$(app_service)"; then
  printf 'Startup failed for topology %s. Recent application logs:\n' "$TOPOLOGY" >&2
  compose logs --no-color --tail=100 "$(app_service)" >&2 || true
  exit 1
fi

uv run --frozen python scripts/wait_for_http.py \
  "${BASE_URL}/health/ready" \
  --timeout 60

printf 'Flask and Valkey are ready: topology=%s url=%s\n' "$TOPOLOGY" "$BASE_URL"

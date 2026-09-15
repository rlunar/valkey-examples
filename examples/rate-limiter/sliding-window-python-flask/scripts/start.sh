#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

start_host_app \
  "$APP_DISPLAY_NAME" \
  "http://${APP_HOST}:${APP_PORT}/health/ready" \
  uv run --frozen rate-limiter-demo

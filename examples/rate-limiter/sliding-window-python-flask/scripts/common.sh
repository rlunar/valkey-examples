#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export CAPSULE_ID="sliding-window-python-flask"
export CAPSULE_INFRA_PROFILES="valkey-standalone-host"
export INFRA_PROFILE="valkey-standalone-host"
export VALKEY_IMAGE="valkey/valkey:9-trixie@sha256:70739f85ad2ee01a726a965584a0f94895f01b0c60b3cc8b0aeef11eaa6888cf"

# shellcheck source=../../../infra/scripts/capsule.sh
source "$capsule_root/../../../infra/scripts/capsule.sh"
# shellcheck source=../../../infra/scripts/rate-limiter.sh
source "$INFRA_ROOT/scripts/rate-limiter.sh"

load_dotenv_defaults .env \
  RATE_LIMIT_IMPLEMENTATION RATE_LIMIT_REQUESTS RATE_LIMIT_WINDOW_MS \
  RATE_LIMIT_POLICY_ID RATE_LIMIT_KEY_PREFIX RATE_LIMIT_MAX_RETRIES \
  VALKEY_HOST VALKEY_PORT VALKEY_REQUEST_TIMEOUT_MS FLASK_HOST FLASK_PORT

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
export APP_HOST="$FLASK_HOST"
export APP_PORT="$FLASK_PORT"
export APP_DISPLAY_NAME="Flask"
export PROCESS_MARKER="rate-limiter-demo"

export RUNTIME_DIR="$capsule_root/.runtime"
export PID_FILE="$RUNTIME_DIR/app.pid"
export LOG_FILE="$RUNTIME_DIR/app.log"
export DEMO_LOCK_DIR="$RUNTIME_DIR/demo.lock"

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  capsule_command "$@"
fi

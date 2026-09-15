#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

start_compose_app "$(app_service)" "${BASE_URL}/" "Flask and Valkey"

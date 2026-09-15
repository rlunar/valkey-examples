#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
# shellcheck source=../../../infra/scripts/rate-limiter-demo.sh
source "$INFRA_ROOT/scripts/rate-limiter-demo.sh"

run_rate_limiter_demo

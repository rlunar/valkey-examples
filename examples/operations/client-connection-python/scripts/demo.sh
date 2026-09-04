#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose run \
  --rm \
  --no-deps \
  -e VALKEY_MODE="$TOPOLOGY" \
  -e VALKEY_ADDRESSES="$VALKEY_ADDRESSES" \
  -e VALKEY_MESSAGE="$VALKEY_MESSAGE" \
  app

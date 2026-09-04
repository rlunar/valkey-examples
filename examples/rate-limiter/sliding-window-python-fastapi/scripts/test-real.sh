#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

cleanup() {
  compose down --remove-orphans
}
trap cleanup EXIT INT TERM

compose up -d --wait valkey
uv run --frozen pytest tests --cov --cov-report=term-missing

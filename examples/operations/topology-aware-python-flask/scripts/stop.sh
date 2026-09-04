#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_all down --remove-orphans --volumes
printf 'Stopped resources owned by topology-aware-python-flask.\n'

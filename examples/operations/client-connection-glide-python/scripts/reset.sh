#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

demo_key="valkey-examples:client-connection:message"

if [[ "$TOPOLOGY" == "cluster" ]]; then
  compose exec -T cluster-node-1 valkey-cli -c del "$demo_key" >/dev/null
else
  compose exec -T standalone valkey-cli del "$demo_key" >/dev/null
fi

printf 'Deleted the demo key.\n'

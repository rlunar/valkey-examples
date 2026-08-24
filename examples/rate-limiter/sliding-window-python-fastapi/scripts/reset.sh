#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

pattern="${RATE_LIMIT_KEY_PREFIX}:*"
deleted="$(
  compose exec -T valkey valkey-cli --raw EVAL \
    "local c='0'; local n=0; repeat local r=redis.call('SCAN',c,'MATCH',ARGV[1],'COUNT',100); c=r[1]; for _,k in ipairs(r[2]) do n=n+redis.call('DEL',k); end; until c=='0'; return n" \
    0 "$pattern"
)"
printf 'Deleted %s rate-limit key(s) matching %s\n' "$deleted" "$pattern"

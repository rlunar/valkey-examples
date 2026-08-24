#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
fake_bin="$test_root/bin"
call_count_file="$test_root/http-call-count"
demo_output="$test_root/demo-output"
mkdir -p "$fake_bin"

cleanup() {
  rm -f \
    "$fake_bin/docker" \
    "$fake_bin/http" \
    "$fake_bin/make" \
    "$fake_bin/sleep" \
    "$fake_bin/uv" \
    "$call_count_file" \
    "$demo_output"
  rmdir "$fake_bin" "$test_root"
}
trap cleanup EXIT

cat >"$fake_bin/make" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF

cat >"$fake_bin/uv" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
  printf 'uv 0.0.0-test\n'
elif [[ "${1:-}" == "python" && "${2:-}" == "find" ]]; then
  printf '/tmp/python3.13-test\n'
fi
EOF

cat >"$fake_bin/docker" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
  printf 'Docker version test\n'
elif [[ "${1:-}" == "compose" && "${2:-}" == "version" ]]; then
  if [[ "${3:-}" == "--short" ]]; then
    printf 'test\n'
  fi
elif [[ "${1:-}" == "compose" && "${2:-}" == "exec" ]]; then
  printf 'test-key\n5\n'
fi
EOF

cat >"$fake_bin/sleep" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF

cat >"$fake_bin/http" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--version" ]]; then
  printf 'HTTPie test\n'
  exit 0
fi

count=0
if [[ -f "$DEMO_HTTP_CALL_COUNT_FILE" ]]; then
  count="$(cat "$DEMO_HTTP_CALL_COUNT_FILE")"
fi
count=$((count + 1))
printf '%s\n' "$count" >"$DEMO_HTTP_CALL_COUNT_FILE"

status=200
retry_after=""
case "$count" in
  6 | 8)
    status=429
    retry_after=1
    ;;
esac

if [[ "$status" == "200" ]]; then
  printf 'HTTP/1.1 200 OK\r\n'
  printf 'RateLimit-Remaining: 1\r\n'
  printf '\r\n'
  printf '{"allowed":true}\n'
else
  printf 'HTTP/1.1 429 TOO MANY REQUESTS\r\n'
  printf 'Retry-After: %s\r\n' "$retry_after"
  printf '\r\n'
  printf '{"allowed":false,"retry_after_ms":1000}\n'
fi
EOF

chmod +x "$fake_bin"/*
export DEMO_HTTP_CALL_COUNT_FILE="$call_count_file"

PATH="$fake_bin:/usr/bin:/bin" CI=1 "$capsule_root/scripts/demo.sh" >"$demo_output"

[[ "$(cat "$call_count_file")" == "9" ]]
grep -q "✅ 200 Accepted" "$demo_output"
grep -q "❌ 429 Denied" "$demo_output"
grep -q "🔑 test-key" "$demo_output"
printf 'Demo follows repeated Retry-After responses until HTTP 200.\n'

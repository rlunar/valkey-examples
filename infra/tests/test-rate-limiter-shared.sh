#!/usr/bin/env bash

set -euo pipefail

infra_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repository_root="$(cd "$infra_root/.." && pwd)"
test_root="$(mktemp -d)"
fake_bin="$test_root/bin"
call_count_file="$test_root/http-call-count"
demo_output="$test_root/demo-output"
mkdir -p "$fake_bin"

cleanup() {
  rm -rf "$test_root"
}
trap cleanup EXIT

capsule_root="$repository_root/examples/rate-limiter/sliding-window-python-flask"
CAPSULE_ID="sliding-window-python-flask"
CAPSULE_INFRA_PROFILES="valkey-standalone-host"
INFRA_PROFILE="valkey-standalone-host"
export capsule_root CAPSULE_ID CAPSULE_INFRA_PROFILES INFRA_PROFILE

# shellcheck source=scripts/capsule.sh
source "$infra_root/scripts/capsule.sh"
# shellcheck source=scripts/rate-limiter.sh
source "$infra_root/scripts/rate-limiter.sh"

response="$(
  printf 'HTTP/1.1 429 Too Many Requests\r\n'
  printf 'Retry-After: 10\r\n\r\n'
  printf '{"allowed":false}\n'
)"
[[ "$(http_status_from_response <<<"$response")" == "429" ]]
[[ "$(retry_after_from_response <<<"$response")" == "10" ]]
[[ "$(CI=1 request_outcome 200 "accepted")" == "✅ 200 Accepted — accepted" ]]
[[ "$(printf 'hashed-key\n5\n' | format_key_state)" == $'🔑 hashed-key\n   members: 5' ]]

mkdir -p "$fake_bin"
for command_name in make sleep; do
  printf '#!/usr/bin/env bash\nexit 0\n' >"$fake_bin/$command_name"
done

cat >"$fake_bin/uv" <<'EOF'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
  printf 'uv 0.0.0-test\n'
elif [[ "${1:-}" == "python" && "${2:-}" == "find" ]]; then
  printf '/tmp/python3.14-test\n'
fi
EOF

cat >"$fake_bin/docker" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"--version"* ]]; then
  printf 'Docker version test\n'
elif [[ "$*" == *"version --short"* ]]; then
  printf 'test\n'
elif [[ " $* " == *" exec "* ]]; then
  printf 'test-key\n5\n'
fi
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
  count="$(<"$DEMO_HTTP_CALL_COUNT_FILE")"
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

printf 'HTTP/1.1 %s TEST\r\n' "$status"
if [[ -n "$retry_after" ]]; then
  printf 'Retry-After: %s\r\n' "$retry_after"
fi
printf '\r\n{"allowed":%s}\n' "$([[ "$status" == "200" ]] && printf true || printf false)"
EOF

chmod +x "$fake_bin"/*
export DEMO_HTTP_CALL_COUNT_FILE="$call_count_file"

for capsule_root in \
  "$repository_root/examples/rate-limiter/sliding-window-python-flask" \
  "$repository_root/examples/rate-limiter/sliding-window-python-fastapi"; do
  rm -f "$call_count_file" "$demo_output"
  PATH="$fake_bin:/usr/bin:/bin" CI=1 \
    "$capsule_root/scripts/demo.sh" >"$demo_output"
  [[ "$(<"$call_count_file")" == "9" ]]
  grep -q "✅ 200 Accepted" "$demo_output"
  grep -q "❌ 429 Denied" "$demo_output"
  grep -q "🔑 test-key" "$demo_output"
done

printf 'Shared rate-limiter orchestration is valid.\n'

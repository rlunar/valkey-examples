#!/usr/bin/env bash

# Shared lifecycle helpers for every capsule.
#
# Most learners can use the Make targets without reading this file. If you do
# read it, follow compose() -> start_compose_app() or start_host_app() ->
# stop_capsule() or stop_host_app().

if [[ -n "${VALKEY_EXAMPLES_CAPSULE_SH_LOADED:-}" ]]; then
  return 0
fi
readonly VALKEY_EXAMPLES_CAPSULE_SH_LOADED=1

: "${capsule_root:?Set capsule_root before sourcing infra/scripts/capsule.sh}"
: "${CAPSULE_ID:?Set CAPSULE_ID before sourcing infra/scripts/capsule.sh}"

INFRA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLS_CERT_DIR="${TLS_CERT_DIR:-$INFRA_ROOT/.cache/tls}"
export INFRA_ROOT CAPSULE_ID TLS_CERT_DIR

ensure_tls_material() {
  local action="${1:-}"

  [[ "${INFRA_PROFILE:-}" == *tls* ]] || return 0
  case "$action" in
    create | exec | run | start | up)
      "$INFRA_ROOT/scripts/generate-tls-certs.sh" "$TLS_CERT_DIR"
      ;;
  esac
}

compose_base() {
  local args=(
    docker compose
    --project-name "valkey-example-${CAPSULE_ID}"
    --project-directory "$capsule_root"
  )

  if [[ -f "$capsule_root/compose.yaml" ]]; then
    args+=(-f "$capsule_root/compose.yaml")
  fi
  args+=(-f "$INFRA_ROOT/compose.yaml")

  printf '%s\0' "${args[@]}"
}

compose() {
  local args=()
  local item

  # Let the calling capsule choose its infrastructure profile.
  if declare -F configure_infra_profile >/dev/null; then
    configure_infra_profile
  fi
  ensure_tls_material "$@"

  while IFS= read -r -d '' item; do
    args+=("$item")
  done < <(compose_base)

  if [[ -n "${TOPOLOGY:-}" ]]; then
    args+=(--profile "$TOPOLOGY")
  fi
  if [[ -n "${INFRA_PROFILE:-}" ]]; then
    args+=(--profile "$INFRA_PROFILE")
  fi

  "${args[@]}" "$@"
}

compose_all() {
  local args=()
  local item
  local profile

  while IFS= read -r -d '' item; do
    args+=("$item")
  done < <(compose_base)

  for profile in ${CAPSULE_TOPOLOGIES:-}; do
    args+=(--profile "$profile")
  done
  for profile in ${CAPSULE_INFRA_PROFILES:-}; do
    args+=(--profile "$profile")
  done

  "${args[@]}" "$@"
}

read_dotenv_value() {
  local name="$1"
  local value

  [[ -f .env ]] || return 1
  value="$(awk -F= -v key="$name" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' .env)"
  [[ -n "$value" ]] || return 1
  value="${value%$'\r'}"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s\n' "$value"
}

load_dotenv_defaults() {
  local dotenv_file="$1"
  shift
  local allowed=" $* "
  local line
  local name
  local value

  [[ -f "$dotenv_file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line#export }"
    [[ "$line" == *=* ]] || continue
    name="${line%%=*}"
    value="${line#*=}"

    case "$allowed" in
      *" $name "*) ;;
      *) continue ;;
    esac

    if [[ -z "${!name+x}" ]]; then
      if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
      fi
      printf -v "$name" '%s' "$value"
      export "${name?}"
    fi
  done <"$dotenv_file"
}

app_service() {
  printf 'app-%s\n' "$TOPOLOGY"
}

wait_for_http() {
  local url="$1"
  local timeout="${2:-60}"
  uv run --frozen python "$INFRA_ROOT/scripts/wait_for_http.py" \
    "$url" --timeout "$timeout"
}

start_compose_app() {
  local service="$1"
  local ready_url="$2"
  local display_name="$3"

  if ! compose up -d --build --wait "$service"; then
    printf 'Startup failed for topology %s. Recent application logs:\n' \
      "$TOPOLOGY" >&2
    compose logs --no-color --tail=100 "$service" >&2 || true
    exit 1
  fi

  wait_for_http "$ready_url" 60
  printf '%s ready: topology=%s url=%s\n' \
    "$display_name" "$TOPOLOGY" "${BASE_URL:-$ready_url}"
}

stop_capsule() {
  compose_all down --remove-orphans --volumes
  printf 'Stopped resources owned by %s.\n' "$CAPSULE_ID"
}

free_port() {
  uv run --frozen python -c \
    'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
}

verify_compose_app_topologies() {
  local topology
  local test_port
  local base_url

  cleanup_compose_app() {
    compose_all down --remove-orphans --volumes >/dev/null 2>&1 || true
  }
  trap cleanup_compose_app EXIT INT TERM

  for topology in $CAPSULE_TOPOLOGIES; do
    test_port="$(free_port)"
    base_url="http://127.0.0.1:${test_port}"

    printf '\n== Verify %s topology ==\n' "$topology"
    cleanup_compose_app

    TOPOLOGY="$topology" FLASK_PORT="$test_port" BASE_URL="$base_url" \
      ./scripts/start.sh

    TOPOLOGY="$topology" FLASK_PORT="$test_port" \
      compose run --rm --no-deps "app-$topology" pytest tests/integration

    BASE_URL="$base_url" EXPECTED_TOPOLOGY="$topology" \
      uv run --frozen pytest tests/journey

    TOPOLOGY="$topology" FLASK_PORT="$test_port" ./scripts/stop.sh
  done
}

is_owned_app_process() {
  local process_id="$1"
  local process_command

  [[ "$process_id" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$process_id" 2>/dev/null || return 1
  process_command="$(ps -p "$process_id" -o command= 2>/dev/null || true)"
  [[ "$process_command" == *"$capsule_root"* ]] &&
    [[ "$process_command" == *"$PROCESS_MARKER"* ]]
}

start_host_app() {
  local display_name="$1"
  local ready_url="$2"
  shift 2
  local existing_pid
  local app_pid

  mkdir -p "$RUNTIME_DIR"

  # Reuse a healthy process that this capsule already started.
  if [[ -f "$PID_FILE" ]]; then
    existing_pid="$(<"$PID_FILE")"
    if is_owned_app_process "$existing_pid"; then
      if ! wait_for_http "$ready_url" 3; then
        printf 'Recorded %s process %s is not healthy; run make stop first.\n' \
          "$display_name" "$existing_pid" >&2
        exit 1
      fi
      printf '%s is already running with PID %s\n' "$display_name" "$existing_pid"
      return 0
    fi
    if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
      printf 'Ignoring stale PID file: process %s is not owned by this capsule.\n' \
        "$existing_pid" >&2
    fi
    rm -f "$PID_FILE"
  fi

  # Start Valkey first, then run the Python web application on the host.
  compose up -d --wait valkey

  "$@" >"$LOG_FILE" 2>&1 &
  app_pid=$!
  printf '%s\n' "$app_pid" >"$PID_FILE"

  if ! wait_for_http "$ready_url" 30; then
    kill "$app_pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    printf '%s failed to become ready. Log output:\n' "$display_name" >&2
    tail -50 "$LOG_FILE" >&2 || true
    exit 1
  fi

  printf 'Valkey and %s are ready (implementation=%s, PID=%s).\n' \
    "$display_name" "$RATE_LIMIT_IMPLEMENTATION" "$app_pid"
}

stop_host_app() {
  local app_pid

  # Stop only a process whose command proves it belongs to this capsule.
  if [[ -f "$PID_FILE" ]]; then
    app_pid="$(<"$PID_FILE")"
    if is_owned_app_process "$app_pid"; then
      kill "$app_pid"
      for _attempt in {1..50}; do
        if ! kill -0 "$app_pid" 2>/dev/null; then
          break
        fi
        sleep 0.1
      done
    elif [[ "$app_pid" =~ ^[0-9]+$ ]] && kill -0 "$app_pid" 2>/dev/null; then
      printf 'Did not stop PID %s because it is not owned by this capsule.\n' \
        "$app_pid" >&2
    fi
    rm -f "$PID_FILE"
  fi

  compose down --remove-orphans
  printf 'Stopped resources owned by %s.\n' "$CAPSULE_ID"
}

capsule_command() {
  case "${1:-}" in
    config)
      compose_all config --quiet
      ;;
    *)
      printf 'Usage: %s config\n' "$0" >&2
      return 2
      ;;
  esac
}

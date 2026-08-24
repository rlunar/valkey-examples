#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

missing=0
for command_name in make docker uv http; do
  if ! command -v "$command_name" >/dev/null; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    missing=1
  fi
done

if (( missing )); then
  printf '\nInstall uv and HTTPie with Homebrew on macOS:\n  brew bundle\n' >&2
  printf 'Docker Desktop or another Docker Engine with Compose v2 must also be running.\n' >&2
  exit 1
fi

docker compose version >/dev/null
docker info >/dev/null

printf 'uv:      %s\n' "$(uv --version)"
printf 'python:  %s\n' "$(uv python find 3.14)"
printf 'docker:  %s\n' "$(docker --version)"
printf 'compose: %s\n' "$(docker compose version --short)"
printf 'httpie:  %s\n' "$(http --version | head -1)"

optional_missing=()
for command_name in gum bat jq yq vhs shellcheck; do
  if ! command -v "$command_name" >/dev/null; then
    optional_missing+=("$command_name")
  fi
done

if (( ${#optional_missing[@]} )); then
  printf 'Optional presentation tools not found: %s (run brew bundle)\n' \
    "${optional_missing[*]}"
fi

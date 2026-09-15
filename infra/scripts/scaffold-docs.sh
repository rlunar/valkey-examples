#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$script_dir/.." && pwd)"
repository_root="$(cd "$infra_root/.." && pwd)"
template_root="$repository_root/docs/templates"

usage() {
  printf 'Usage: %s CAPSULE_PATH\n' "${0##*/}" >&2
}

[[ $# -eq 1 ]] || {
  usage
  exit 2
}

requested_path="$1"
if [[ "$requested_path" == /* ]]; then
  capsule_root="$requested_path"
elif [[ -d "$requested_path" ]]; then
  capsule_root="$(cd "$requested_path" && pwd)"
elif [[ -d "$repository_root/$requested_path" ]]; then
  capsule_root="$(cd "$repository_root/$requested_path" && pwd)"
else
  printf 'Capsule directory does not exist: %s\n' "$requested_path" >&2
  exit 2
fi

for required_file in README.md Makefile; do
  if [[ ! -s "$capsule_root/$required_file" ]]; then
    printf 'Capsule is missing %s: %s\n' "$required_file" "$capsule_root" >&2
    exit 2
  fi
done

for document in DEMO.md TUTORIAL.md SCRIPT_REEL.md SCRIPT_VIDEO.md VIDEO.md; do
  if [[ ! -s "$template_root/$document" ]]; then
    printf 'Documentation template is missing: %s\n' "$template_root/$document" >&2
    exit 2
  fi
done

if ! grep -Eq '^demo[[:space:]]*:' "$capsule_root/Makefile"; then
  printf 'Capsule Makefile must expose a demo target: %s\n' "$capsule_root" >&2
  exit 2
fi

capsule_id="$(basename "$capsule_root")"
capsule_title="$(
  awk '/^# / { sub(/^# /, ""); print; exit }' "$capsule_root/README.md"
)"
if [[ -z "$capsule_title" ]]; then
  capsule_title="${capsule_id//-/ }"
fi

mkdir -p "$capsule_root/docs"

created=0
for document in DEMO.md TUTORIAL.md SCRIPT_REEL.md SCRIPT_VIDEO.md VIDEO.md; do
  template="$template_root/$document"
  target="$capsule_root/docs/$document"

  if [[ -e "$target" ]]; then
    printf 'Keeping existing %s.\n' "$target"
    continue
  fi

  python3 - "$template" "$target" "$capsule_title" "$capsule_id" <<'PY'
from pathlib import Path
import sys

template_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
capsule_title = sys.argv[3]
capsule_id = sys.argv[4]

rendered = (
    template_path.read_text()
    .replace("{{CAPSULE_TITLE}}", capsule_title)
    .replace("{{CAPSULE_ID}}", capsule_id)
)
target_path.write_text(rendered)
PY
  printf 'Created %s.\n' "$target"
  created=$((created + 1))
done

if ((created == 0)); then
  printf 'Documentation already exists; nothing changed.\n'
else
  printf 'Created %s documentation file(s) for %s.\n' "$created" "$capsule_id"
fi

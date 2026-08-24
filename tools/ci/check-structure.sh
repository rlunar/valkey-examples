#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repository_root"

required_files=(
  README.md
  CONTRIBUTING.md
  MAINTAINERS.md
  SECURITY.md
  SUPPORT.md
  COMPATIBILITY.md
  compatibility.yaml
  schemas/example.schema.json
  schemas/compatibility.schema.json
)

for required_file in "${required_files[@]}"; do
  if [[ ! -s "$required_file" ]]; then
    echo "Required file is missing or empty: $required_file" >&2
    exit 1
  fi
done

python3 -m json.tool schemas/example.schema.json >/dev/null
python3 -m json.tool schemas/compatibility.schema.json >/dev/null

while IFS= read -r -d '' manifest; do
  capsule_dir="$(dirname "$manifest")"

  for capsule_file in README.md Makefile; do
    if [[ ! -s "$capsule_dir/$capsule_file" ]]; then
      echo "Capsule is missing $capsule_file: $capsule_dir" >&2
      exit 1
    fi
  done
done < <(find examples -type f -name example.yaml -print0)

empty_directories="$(
  find . \
    -path ./.git -prune -o \
    -type d -empty -print
)"

if [[ -n "$empty_directories" ]]; then
  echo "Empty directories are not allowed:" >&2
  echo "$empty_directories" >&2
  exit 1
fi

echo "Repository structure is valid."

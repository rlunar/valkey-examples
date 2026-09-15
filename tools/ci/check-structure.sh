#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repository_root"

required_files=(
  AGENTS.md
  README.md
  CONTRIBUTING.md
  MAINTAINERS.md
  SECURITY.md
  SUPPORT.md
  COMPATIBILITY.md
  compatibility.yaml
  CONTEXT.md
  docs/authoring.md
  schemas/example.schema.json
  schemas/compatibility.schema.json
  docs/templates/README.md
  docs/templates/DEMO.md
  docs/templates/TUTORIAL.md
  docs/templates/SCRIPT_REEL.md
  docs/templates/SCRIPT_VIDEO.md
  docs/templates/VIDEO.md
  infra/README.md
  infra/Makefile
  infra/compose.yaml
  infra/docs/README.md
  infra/docs/DESIGN.md
  infra/docs/standalone/DEMO.md
  infra/docs/standalone/TUTORIAL.md
  infra/docs/standalone/SCRIPT_REEL.md
  infra/docs/standalone/SCRIPT_VIDEO.md
  infra/docs/sentinel/DEMO.md
  infra/docs/sentinel/TUTORIAL.md
  infra/docs/sentinel/SCRIPT_REEL.md
  infra/docs/sentinel/SCRIPT_VIDEO.md
  infra/docs/cluster/DEMO.md
  infra/docs/cluster/TUTORIAL.md
  infra/docs/cluster/SCRIPT_REEL.md
  infra/docs/cluster/SCRIPT_VIDEO.md
  infra/make/python.mk
  infra/scripts/capsule.sh
  infra/scripts/demo-deployment.sh
  infra/scripts/scaffold-docs.sh
  infra/scripts/generate-tls-certs.sh
  infra/scripts/validate-valkey.sh
  infra/tests/test-deployment-demos-real.sh
  infra/tests/test-docs-shared.sh
  infra/tests/test-infra-real.sh
  infra/valkey/valkey.conf
  infra/valkey/valkey-tls.conf
)

for required_file in "${required_files[@]}"; do
  if [[ ! -s "$required_file" ]]; then
    echo "Required file is missing or empty: $required_file" >&2
    exit 1
  fi
done

if [[ -d infra/docs/templates ]]; then
  echo "Documentation templates belong under docs/templates, not infra/docs." >&2
  exit 1
fi

for writing_tenet in \
  '## Use active voice and second person' \
  '## Use pop culture as a memory hook'; do
  if ! grep -qx "$writing_tenet" docs/authoring.md; then
    echo "Authoring guidance is missing a writing tenet: $writing_tenet" >&2
    exit 1
  fi
done

python3 -m json.tool schemas/example.schema.json >/dev/null
python3 -m json.tool schemas/compatibility.schema.json >/dev/null

while IFS= read -r -d '' manifest; do
  capsule_dir="$(dirname "$manifest")"
  schema_version="$(
    awk '/^schema_version:/ { print $2; exit }' "$manifest"
  )"
  level="$(
    awk '/^level:/ { print $2; exit }' "$manifest"
  )"
  readme_level="$(
    awk '
      /^\*\*Level:\*\*/ {
        for (field = 1; field <= NF; field += 1) {
          if ($field ~ /`L[1-5]00`/) {
            gsub(/[^A-Z0-9]/, "", $field)
            print $field
            exit
          }
        }
      }
    ' "$capsule_dir/README.md"
  )"
  infrastructure_capsule="$(
    awk '
      /^infrastructure:/ { in_infrastructure = 1; next }
      in_infrastructure && /^  capsule:/ {
        sub(/^  capsule:[[:space:]]*/, "")
        print
        exit
      }
      in_infrastructure && /^[^[:space:]]/ { exit }
    ' "$manifest"
  )"

  for capsule_file in \
    README.md \
    Makefile \
    docs/SCRIPT_REEL.md \
    docs/SCRIPT_VIDEO.md; do
    if [[ ! -s "$capsule_dir/$capsule_file" ]]; then
      echo "Capsule is missing $capsule_file: $capsule_dir" >&2
      exit 1
    fi
  done

  if [[ "$infrastructure_capsule" != "../../../infra" ]]; then
    echo "Capsule must point to ../../../infra: $capsule_dir" >&2
    exit 1
  fi

  if [[ "$schema_version" != "2" ]]; then
    echo "Capsule must use example schema version 2: $capsule_dir" >&2
    exit 1
  fi

  case "$level" in
    L100 | L200 | L300 | L400 | L500) ;;
    *)
      echo "Capsule has an invalid or missing level: $capsule_dir" >&2
      exit 1
      ;;
  esac

  if [[ "$readme_level" != "$level" ]]; then
    echo "Capsule README level must match example.yaml: $capsule_dir" >&2
    exit 1
  fi

  if ! grep -qx '## Start here' "$capsule_dir/README.md"; then
    echo "Capsule README must include a plain-language 'Start here' section: $capsule_dir" >&2
    exit 1
  fi

  if [[ -f "$capsule_dir/docs/TUTORIAL.md" ]] &&
    ! grep -qx '## Read this first' "$capsule_dir/docs/TUTORIAL.md"; then
    echo "Capsule tutorial must include a plain-language 'Read this first' section: $capsule_dir" >&2
    exit 1
  fi

  if ! grep -q 'Target duration: 60 seconds maximum' \
    "$capsule_dir/docs/SCRIPT_REEL.md"; then
    echo "Capsule reel script must declare a 60-second maximum: $capsule_dir" >&2
    exit 1
  fi

  if ! grep -q 'Primary build complete by: 05:00' \
    "$capsule_dir/docs/SCRIPT_VIDEO.md"; then
    echo "Capsule tutorial-video script must complete its primary build by 05:00: $capsule_dir" >&2
    exit 1
  fi

  if [[ ! -d "$capsule_dir/$infrastructure_capsule" ]]; then
    echo "Infrastructure capsule does not exist: $capsule_dir/$infrastructure_capsule" >&2
    exit 1
  fi
done < <(find examples -type f -name example.yaml -print0)

if ! grep -qx '## Start here' infra/README.md; then
  echo "Infrastructure README must include a plain-language 'Start here' section." >&2
  exit 1
fi

for tutorial in infra/docs/*/TUTORIAL.md; do
  if ! grep -qx '## Read this first' "$tutorial"; then
    echo "Infrastructure tutorial must include a plain-language 'Read this first' section: $tutorial" >&2
    exit 1
  fi
done

for reel in infra/docs/*/SCRIPT_REEL.md; do
  if ! grep -q 'Target duration: 60 seconds maximum' "$reel"; then
    echo "Infrastructure reel script must declare a 60-second maximum: $reel" >&2
    exit 1
  fi
done

for video in infra/docs/*/SCRIPT_VIDEO.md; do
  if ! grep -q 'Primary build complete by: 05:00' "$video"; then
    echo "Infrastructure tutorial-video script must complete its primary build by 05:00: $video" >&2
    exit 1
  fi
done

while IFS= read -r -d '' proposal; do
  level="$(
    awk '/^level:/ { print $2; exit }' "$proposal"
  )"
  case "$level" in
    L100 | L200 | L300 | L400 | L500) ;;
    *)
      echo "Proposal has an invalid or missing level: $proposal" >&2
      exit 1
      ;;
  esac
done < <(
  find docs/proposals -maxdepth 1 -type f -name '*.md' \
    ! -name README.md ! -name AGENTS.md -print0
)

empty_directories="$(
  find . \
    -path ./.git -prune -o \
    -path '*/.artifacts' -prune -o \
    -path '*/.cache' -prune -o \
    -path '*/.pytest_cache' -prune -o \
    -path '*/.ruff_cache' -prune -o \
    -path '*/.runtime' -prune -o \
    -path '*/.venv' -prune -o \
    -path '*/__pycache__' -prune -o \
    -type d -empty -print
)"

if [[ -n "$empty_directories" ]]; then
  echo "Empty directories are not allowed:" >&2
  echo "$empty_directories" >&2
  exit 1
fi

echo "Repository structure is valid."

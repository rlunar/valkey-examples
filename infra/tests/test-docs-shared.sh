#!/usr/bin/env bash

set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_root="$(cd "$test_dir/.." && pwd)"
repository_root="$(cd "$infra_root/.." && pwd)"
temporary_root="$(mktemp -d)"
capsule_root="$temporary_root/example-capsule"

cleanup() {
  rm -rf "$temporary_root"
}
trap cleanup EXIT INT TERM

for document in DEMO.md TUTORIAL.md SCRIPT_REEL.md SCRIPT_VIDEO.md VIDEO.md; do
  test -s "$repository_root/docs/templates/$document"
done
test ! -d "$infra_root/docs/templates"

extract_verbatim_file() {
  local tutorial="$1"
  local source_path="$2"
  local source_file="$repository_root/$source_path"
  local extracted_file

  extracted_file="$temporary_root/$(basename "$(dirname "$tutorial")")-$(basename "$source_path")"

  awk \
    -v begin="<!-- BEGIN VERBATIM: $source_path -->" \
    -v end="<!-- END VERBATIM: $source_path -->" '
      $0 == begin {
        capture = 1
        next
      }
      $0 == end {
        capture = 0
        found = 1
      }
      capture {
        print
      }
      END {
        if (!found) {
          exit 1
        }
      }
    ' "$tutorial" |
    sed '1d;$d' >"$extracted_file"

  cmp "$source_file" "$extracted_file"
}

for tutorial in "$infra_root"/docs/*/TUTORIAL.md; do
  if grep -Eq '\]\(\.\.?/' "$tutorial"; then
    printf 'Infrastructure tutorial contains a local-file link: %s\n' \
      "$tutorial" >&2
    exit 1
  fi

  extract_verbatim_file "$tutorial" "infra/valkey/valkey.conf"
done

for demo in "$infra_root"/docs/*/DEMO.md; do
  grep -q 'glow - --width 100' "$demo"
  grep -q 'yq -C' "$demo"
  grep -q 'bat --paging=never --style=numbers' "$demo"
  grep -q 'gum style --bold' "$demo"
done

for reel in "$infra_root"/docs/*/SCRIPT_REEL.md; do
  grep -q 'Target duration: 60 seconds maximum' "$reel"
  grep -q 'make demo' "$reel"
done

for video in "$infra_root"/docs/*/SCRIPT_VIDEO.md; do
  grep -q 'Primary build complete by: 05:00' "$video"
  grep -q 'make demo' "$video"
done

extract_verbatim_file \
  "$infra_root/docs/standalone/TUTORIAL.md" \
  "infra/valkey/valkey-tls.conf"
extract_verbatim_file \
  "$infra_root/docs/sentinel/TUTORIAL.md" \
  "infra/sentinel/sentinel.conf"

mkdir -p "$capsule_root"
printf '# Example Capsule\n' >"$capsule_root/README.md"
printf 'demo:\n\t@true\n' >"$capsule_root/Makefile"

"$infra_root/scripts/scaffold-docs.sh" "$capsule_root" >/dev/null

for document in DEMO.md TUTORIAL.md SCRIPT_REEL.md SCRIPT_VIDEO.md VIDEO.md; do
  test -s "$capsule_root/docs/$document"
  grep -q 'Example Capsule' "$capsule_root/docs/$document"
done

before="$(cksum "$capsule_root/docs/DEMO.md")"
"$infra_root/scripts/scaffold-docs.sh" "$capsule_root" >/dev/null
after="$(cksum "$capsule_root/docs/DEMO.md")"

[[ "$before" == "$after" ]]

printf 'Shared documentation scaffolding is valid.\n'

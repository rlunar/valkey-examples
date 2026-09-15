# {{CAPSULE_TITLE}} Demo Runbook

## Observable goal

<!-- TODO: Start with "You will see" and explain why Valkey is material. -->

The demo must use the capsule's real interface:

```shell
make setup
make start
make demo
make reset
make stop
```

## Audience and duration

- Audience: <!-- TODO -->
- Target duration: <!-- TODO -->
- Primary topology: <!-- TODO -->
- Optional variation: <!-- TODO -->

## Prepare before presenting

Run setup and the full verification path before recording:

```shell
make setup
make verify
```

Confirm ports, credentials, deterministic fixtures, and presenter tools. Keep
secrets, personal data, unrelated terminals, and unstable external services
out of the recording.

You may assume Homebrew, HTTPie, bat, Gum, Glow, jq, and yq are installed.

## Presentation path

### 1. Orient your audience

Do not point to a file without displaying it. Replace these placeholders with
the exact commands and queries for this capsule:

```shell
gum style --bold "Architecture"
glow README.md

gum style --bold "Implementation"
bat --paging=never --style=numbers PATH_TO_SOURCE

gum style --bold "Configuration"
yq -C 'YQ_QUERY' PATH_TO_YAML
jq -C 'JQ_QUERY' PATH_TO_JSON
```

<!-- TODO: Remove unused commands and tell the audience what to notice in each output. -->

### 2. Start the demo

```shell
make start
```

Expected readiness evidence:

```text
TODO
```

### 3. Show the Valkey behavior

```shell
make demo
```

Expected observable output:

```text
TODO
```

Suggested narration:

> TODO

### 4. Clean up

```shell
make reset
make stop
```

## Failure or contrast path

<!-- TODO: Include one useful denial, validation failure, retry, or topology variation. -->

## Recovery

Document bounded recovery commands for port conflicts, startup failures, and
capsule-owned cleanup. Do not recommend broad container or keyspace deletion.

## Pre-publication checklist

- [ ] `make verify` passes.
- [ ] Every shown command was rerun from the capsule root.
- [ ] Expected output matches the current implementation.
- [ ] Cleanup leaves no capsule containers or generated secrets.
- [ ] Source excerpts and diagrams are readable at the target resolution.
- [ ] Every referenced file has an exact command that displays its content.
- [ ] Narration addresses the audience as "you" and uses active voice.
- [ ] Any pop culture reference clarifies the idea without replacing it.

# Validated Object Storage Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: typed-object architecture, cached deployment, two successes, one rejection
- Behavioral source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)

Use the replicated standalone topology for the reel.

## Prepare off camera

```shell
cp -n .env.example .env
make setup
make verify
make start
make stop
```

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:06 | Title: “Validate before Valkey writes” | “Valkey stores bytes. Pydantic decides whether this object is safe to store.” | Hook |
| 00:06–00:17 | Show the product variants and storage adapter | “The `kind` field selects a physical or digital model. Valid objects become JSON strings in Valkey.” | Architecture |
| 00:17–00:33 | Run `make start` | “The cached build deploys Flask with a primary and replica.” | Readiness |
| 00:33–00:54 | Run `make demo` | “Both product types round-trip into their original classes. Negative stock fails with HTTP 422 before SET runs.” | `201`, `200`, `422` |
| 00:54–01:00 | Hold the three outcomes | “Typed in, typed out, and invalid data never reaches Valkey.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Pydantic variants and Valkey JSON"
bat --paging=never --style=numbers \
  --highlight-line 52:72 \
  src/validated_objects/models.py
bat --paging=never --style=numbers \
  --highlight-line 43:54 \
  src/validated_objects/valkey_client.py

make start
make demo
```

## After recording

```shell
make reset
make stop
```

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] Physical and digital round trips are visible.
- [ ] HTTP 422 appears before the closing line.
- [ ] The narration states that Valkey stores JSON bytes, not Python objects.

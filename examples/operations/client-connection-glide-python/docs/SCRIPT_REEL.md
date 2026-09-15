# Minimal Valkey GLIDE Python Connection Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Planned duration: 40–45 seconds
- Timed scope: one-file architecture, cached deployment, `SET`/`GET`, takeaway
- Behavioral source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)

Record standalone and cluster as separate takes.

## Prepare off camera

```shell
make setup
make verify
make start
make stop
```

Keep the default standalone values in `.env`.

## 45-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:05 | Title: “Python to Valkey in one file” | “This is the smallest useful Valkey GLIDE program.” | Hook |
| 00:05–00:14 | Show `create_client()` and the command path | “Dotenv selects standalone or cluster. GLIDE creates the matching client.” | Architecture |
| 00:14–00:27 | Run `make start` | “The cached Compose profile deploys real Valkey and waits until it is ready.” | Readiness |
| 00:27–00:38 | Run `make demo` | “The same client runs SET, GET, decodes the bytes, and prints the value.” | `hello from GLIDE` |
| 00:38–00:45 | Show `close()` | “One file, one client, and the connection always closes.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "GLIDE client, SET, GET, and close"
bat --paging=never --style=numbers \
  --highlight-line 23:43 \
  --highlight-line 52:59 \
  src/valkey_connection/app.py

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
- [ ] The take uses exactly one topology.
- [ ] `hello from GLIDE` is visible.
- [ ] The narration names `SET`, `GET`, and client cleanup.

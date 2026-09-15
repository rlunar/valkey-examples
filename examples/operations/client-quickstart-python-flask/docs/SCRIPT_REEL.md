# Valkey GLIDE Flask Quickstart Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: Flask-to-Valkey architecture, cached deployment, HTTP proof
- Behavioral source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)

Use standalone for the reel. Record cluster as a separate variation.

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
| 00:00–00:05 | Title: “Flask plus Valkey GLIDE” | “This Flask route stores and retrieves one value with visible Valkey commands.” | Hook |
| 00:05–00:15 | Show the route and client | “Flask owns HTTP. `ValkeyClient` owns connection construction. The route still calls SET and GET directly.” | Architecture |
| 00:15–00:32 | Run `make start` | “The cached standalone profile deploys a primary, replica, and Flask application.” | Readiness |
| 00:32–00:53 | Run `make demo` | “POST stores the value. GET reads the same value from real Valkey.” | Two HTTP responses |
| 00:53–01:00 | Hold both responses | “One small wrapper, normal GLIDE commands, and a complete Flask round trip.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Flask route and Valkey client"
bat --paging=never --style=numbers \
  --highlight-line 17:37 \
  src/valkey_quickstart/app.py
bat --paging=never --style=numbers \
  --highlight-line 24:37 \
  src/valkey_quickstart/valkey_client.py

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
- [ ] The take uses standalone only.
- [ ] Both POST and GET responses show `hello from standalone`.
- [ ] The narration keeps Flask and GLIDE responsibilities distinct.

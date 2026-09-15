# Flask Sliding-Window Rate Limiter Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 7–9 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Primary implementation: `multi-exec`

The transaction-backed Flask build completes before five minutes. Lua and
concurrency tradeoffs follow as optional deeper chapters.

## Prepare off camera

```shell
make setup
make verify
make stop
```

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:25 | Preview accepted, denied, isolated, and recovered requests | “You will build a Flask endpoint that limits each caller over a rolling window stored in Valkey.” | Finished result |
| 00:25–01:05 | Render the architecture and request flow | “Flask validates identity. A limiter adapter owns the atomic Valkey decision. The HTTP response exposes remaining and retry timing.” | Architecture |
| 01:05–01:50 | Show `RateLimitPolicy` and decision fields | “The policy defines the limit and window. The decision translates Valkey state into HTTP status and headers.” | Domain contract |
| 01:50–03:00 | Walk through `MultiExecRateLimiter.check()` | “The implementation locks the connection, WATCHes the key, reads Valkey time, counts active entries, and executes one atomic batch.” | Transaction algorithm |
| 03:00–03:40 | Show the Flask route | “The route normalizes identity, generates a UUIDv7 request member, calls the limiter, and returns 200 or 429.” | HTTP adapter |
| 03:40–04:40 | Run the shortened `make demo` | “The command deploys Valkey and Flask, proves isolation and denial, waits for the window, and cleans up.” | Real journey |
| 04:40–05:00 | Hold the recovered request | “The transaction-backed primary build is complete.” | Five-minute checkpoint |
| 05:00–06:20 | Lua chapter | “The Lua adapter moves the entire decision into one server-side script while preserving the same contract.” | Alternative implementation |
| 06:20–07:40 | Concurrency and production tradeoffs | “WATCH state is connection-scoped, so the implementation serializes each transaction sequence. Production still needs trusted identity and distributed availability.” | Deeper reasoning |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Configuration$/p' \
  README.md |
  glow - --width 100

bat --paging=never --style=numbers \
  src/rate_limiter_demo/decision.py
bat --paging=never --style=numbers \
  --highlight-line 28:99 \
  src/rate_limiter_demo/valkey/multi_exec.py
bat --paging=never --style=numbers \
  --highlight-line 42:67 \
  src/rate_limiter_demo/app.py

RATE_LIMIT_REQUESTS=3 \
RATE_LIMIT_WINDOW_MS=2000 \
make demo
```

Optional Lua chapter:

```shell
RATE_LIMIT_IMPLEMENTATION=lua \
RATE_LIMIT_REQUESTS=3 \
RATE_LIMIT_WINDOW_MS=2000 \
make demo
```

## Verification

- [ ] The multi-exec journey succeeds before 05:00.
- [ ] Lua begins only after the primary checkpoint.
- [ ] The script explains why the connection lock surrounds WATCH through EXEC.
- [ ] The demo cleans up the host process and Valkey container.

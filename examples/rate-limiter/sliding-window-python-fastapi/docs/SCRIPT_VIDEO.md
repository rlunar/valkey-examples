# FastAPI Sliding-Window Rate Limiter Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 7–9 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Primary implementation: `multi-exec`

The asynchronous transaction-backed build completes before five minutes. Lua
and lifecycle details continue afterward.

## Prepare off camera

```shell
make setup
make verify
make stop
```

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:25 | Preview accepted, denied, isolated, and recovered requests | “You will build an async FastAPI endpoint that makes an exact sliding-window decision in Valkey.” | Finished result |
| 00:25–01:05 | Render the architecture and request flow | “FastAPI owns HTTP and lifespan. The limiter owns atomicity. GLIDE carries asynchronous commands to Valkey.” | Architecture |
| 01:05–01:55 | Show the lifespan function | “Startup creates one client and limiter. The application stores them in state, and shutdown awaits `close()`.” | Connection lifecycle |
| 01:55–03:05 | Walk through `MultiExecRateLimiter.check()` | “An asyncio lock protects the shared client's WATCH state while every Valkey call remains awaitable.” | Transaction algorithm |
| 03:05–03:40 | Show the endpoint | “The endpoint normalizes identity, awaits the decision, and returns rate-limit headers with 200 or 429.” | HTTP adapter |
| 03:40–04:40 | Run the shortened `make demo` | “The command deploys Valkey and FastAPI, proves caller isolation, observes denial, then confirms recovery.” | Real journey |
| 04:40–05:00 | Hold the final accepted request | “The asynchronous primary build is complete.” | Five-minute checkpoint |
| 05:00–06:20 | Lua chapter | “The Lua implementation preserves the async interface while Valkey executes the decision as one script.” | Alternative implementation |
| 06:20–07:40 | Compare lifespan and concurrency tradeoffs | “A process-wide client reduces connection churn, but connection-scoped transaction state must remain serialized.” | Deeper reasoning |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Configuration$/p' \
  README.md |
  glow - --width 100

bat --paging=never --style=numbers \
  --highlight-line 49:105 \
  src/rate_limiter_demo/app.py
bat --paging=never --style=numbers \
  --highlight-line 28:101 \
  src/rate_limiter_demo/valkey/multi_exec.py

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
- [ ] The script explains lifespan ownership and connection-scoped WATCH state.
- [ ] Cleanup closes the FastAPI process and Valkey resources.

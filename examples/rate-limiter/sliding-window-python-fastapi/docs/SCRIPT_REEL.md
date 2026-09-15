# FastAPI Sliding-Window Rate Limiter Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: async architecture, cached deployment, allowed/denied proof, recovery
- Behavioral source: `make demo`
- Primary implementation: `multi-exec`

The reel uses a three-request, two-second policy so the complete behavior fits
the short format.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Cache the pinned Valkey image and Python environment.

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:06 | Title: “Async rate limiting with Valkey” | “FastAPI creates one asynchronous GLIDE client and uses a sorted set as a sliding window.” | Hook |
| 00:06–00:16 | Show lifespan, limiter, and Valkey | “Lifespan owns the client. Each request awaits one limiter decision and shutdown closes the connection.” | Architecture |
| 00:16–00:28 | Show the async transaction core | “An asyncio lock protects connection-scoped WATCH state through EXEC while network commands remain asynchronous.” | Concurrency rule |
| 00:28–00:53 | Run the shortened demo | “Caller A reaches 429, caller B keeps an independent budget, and A is accepted after the window advances.” | `200`, `429`, isolation, recovery |
| 00:53–01:00 | Hold the recovered result | “Async HTTP outside, one atomic Valkey decision inside.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "FastAPI lifespan and async GLIDE"
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

Cut repeated setup output and idle waiting from the final edit, but retain real
startup, HTTP statuses, key state, and recovery.

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] Lifespan creation or cleanup is visible.
- [ ] Accepted, denied, isolated, and recovered outcomes appear.
- [ ] The narration explains the asyncio lock without calling it a database lock.

# Flask Sliding-Window Rate Limiter Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: architecture, cached deployment, allowed/denied proof, recovery
- Behavioral source: `make demo`
- Primary implementation: `multi-exec`

The reel uses a three-request, two-second policy so the complete sliding-window
story fits the short format without changing the algorithm.

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
| 00:00–00:06 | Title: “Rate limit the last two seconds” | “This Flask endpoint uses a Valkey sorted set as a sliding request window.” | Hook |
| 00:06–00:16 | Show Flask, limiter, GLIDE, and Valkey | “Flask identifies the caller. The limiter makes one atomic decision through GLIDE and Valkey.” | Architecture |
| 00:16–00:28 | Show the transaction core | “WATCH detects another writer. MULTI and EXEC trim old timestamps, conditionally add this request, and return the new count.” | Atomic algorithm |
| 00:28–00:53 | Run the shortened demo | “Caller A is accepted three times, then receives 429. Caller B still has a separate budget, and A recovers after the window moves.” | `200`, `429`, isolation, recovery |
| 00:53–01:00 | Hold the final accepted result | “One sorted set per identity gives you an exact rolling window.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Flask to GLIDE to a Valkey sorted set"
sed -n '/^## Architecture$/,/^## Allowed and denied flow$/p' \
  README.md |
  glow - --width 80

bat --paging=never --style=numbers \
  --highlight-line 28:87 \
  src/rate_limiter_demo/valkey/multi_exec.py

RATE_LIMIT_REQUESTS=3 \
RATE_LIMIT_WINDOW_MS=2000 \
make demo
```

Cut repeated setup output and idle waiting from the final edit, but retain the
real startup, HTTP statuses, key state, and recovery result.

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] At least one accepted and one denied request are visible.
- [ ] Caller B proves identity isolation.
- [ ] Caller A is accepted again after the rolling window advances.

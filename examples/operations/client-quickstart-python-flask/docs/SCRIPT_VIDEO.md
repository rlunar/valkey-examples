# Valkey GLIDE Flask Quickstart Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 6–7 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The standalone HTTP journey completes before five minutes. The six-node cluster
is an optional comparison.

## Prepare off camera

```shell
cp -n .env.example .env
make setup
make verify
make stop
```

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:20 | Preview POST and GET output | “You will build one Flask route that stores and retrieves a string through GLIDE.” | Finished result |
| 00:20–01:00 | Render the architecture | “HTTP enters Flask, the route calls a small connection wrapper, and GLIDE sends SET and GET to Valkey.” | Architecture |
| 01:00–01:50 | Show dependencies and `.env` | “The environment selects standalone or cluster without changing route code.” | Build configuration |
| 01:50–02:45 | Walk through `valkey_client.py` | “The wrapper chooses `GlideClient` or `GlideClusterClient` from the configured mode and addresses.” | Client construction |
| 02:45–03:30 | Walk through `app.py` | “POST reads JSON and calls SET. GET calls GET, decodes bytes, and returns JSON.” | HTTP adapter |
| 03:30–04:10 | Run `make start` | “The cached standalone application and replicated Valkey profile become ready.” | Readiness |
| 04:10–04:45 | Run `make demo` | “The prepared journey proves both HTTP requests against real Valkey.” | Behavioral proof |
| 04:45–05:00 | Reset and stop | “The primary build is complete and the known key is removed.” | Five-minute checkpoint |
| 05:00–06:30 | Optional: repeat with `TOPOLOGY=cluster` | “The cluster client changes routing, not the route or commands.” | Variation |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Responsibilities$/p' \
  docs/DESIGN.md |
  glow - --width 90

bat --paging=never --style=numbers .env.example
bat --paging=never --style=numbers \
  --highlight-line 24:37 \
  src/valkey_quickstart/valkey_client.py
bat --paging=never --style=numbers \
  --highlight-line 17:37 \
  src/valkey_quickstart/app.py

make start
make demo
make reset
make stop
```

Optional cluster chapter:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

## Verification

- [ ] The standalone POST/GET journey succeeds before 05:00.
- [ ] Cluster begins only after the primary checkpoint.
- [ ] Source excerpts show the actual GLIDE commands.
- [ ] Cleanup deletes the known key and stops both profiles.

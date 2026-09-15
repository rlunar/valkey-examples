# Topology-Aware Flask Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 8–10 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

Standalone completes before five minutes. Sentinel discovery and cluster
routing are deeper chapters after the primary checkpoint.

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
| 00:00–00:25 | Preview the three topology outputs | “You will keep one Flask counter API unchanged while the store connects through standalone, Sentinel, or cluster.” | Finished result |
| 00:25–01:10 | Render the architecture | “Routes depend on `CounterStore`. `ValkeyStore` selects the client, performs Sentinel discovery when needed, and owns reconnection.” | Architecture |
| 01:10–02:00 | Show settings and topology enum | “Validated settings choose the topology, seed addresses, Sentinel group, database, and timeouts.” | Configuration |
| 02:00–02:50 | Show the store interface and client selection | “The application code sees get, increment, delete, and topology information—not client constructors.” | Adapter boundary |
| 02:50–03:25 | Show the Flask routes | “Every route validates a counter name and calls the same store methods.” | HTTP adapter |
| 03:25–04:05 | Start standalone | “The cached standalone application and Valkey node become ready.” | Readiness |
| 04:05–04:45 | Run the standalone journey | “The app reports `GlideClient`, increments the counter from one to two, and reads two from Valkey.” | Behavioral proof |
| 04:45–05:00 | Reset and stop | “The primary build is complete.” | Five-minute checkpoint |
| 05:00–06:30 | Sentinel chapter | “Sentinel mode asks for the named primary, creates the data client, and can rediscover after a role failure.” | Discovery |
| 06:30–07:45 | Cluster chapter | “Cluster mode uses `GlideClusterClient`; the counter route and key remain unchanged.” | Cluster routing |
| 07:45–09:00 | Observability and tradeoffs | “Structured logs identify topology and operation, while production still needs TLS, ACLs, and first-class Sentinel support.” | Operational boundary |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Module responsibilities$/p' \
  docs/DESIGN.md |
  glow - --width 100

bat --paging=never --style=numbers \
  --highlight-line 31:88 \
  --highlight-line 128:210 \
  src/valkey_flask_demo/store.py
bat --paging=never --style=numbers \
  --highlight-line 111:145 \
  src/valkey_flask_demo/app.py

TOPOLOGY=standalone make start
TOPOLOGY=standalone make demo
TOPOLOGY=standalone make reset
TOPOLOGY=standalone make stop
```

Sentinel chapter:

```shell
TOPOLOGY=sentinel make start
TOPOLOGY=sentinel make demo
TOPOLOGY=sentinel make reset
TOPOLOGY=sentinel make stop
```

Cluster chapter:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

## Verification

- [ ] Standalone succeeds before 05:00.
- [ ] Sentinel and cluster start after the primary checkpoint.
- [ ] The script shows the same route behavior in all three modes.
- [ ] Cleanup stops every profile owned by the capsule.

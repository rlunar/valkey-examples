# Standalone Valkey Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: one-node architecture, cached deployment, command proof, takeaway
- Behavioral source: `make demo-standalone`
- Runbook source: [`DEMO.md`](DEMO.md)

## Prepare off camera

Run from `infra/`:

```shell
make setup
make verify
make start PROFILE=valkey-standalone
make stop
```

The warm start keeps image downloads and verification outside the reel.

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:05 | Title: “The smallest Valkey deployment” | “How small can a Valkey deployment be? One writable process.” | Hook |
| 00:05–00:13 | Show the resolved `standalone` service | “Compose starts one node with shared memory limits, health checks, and disposable data.” | Architecture |
| 00:13–00:27 | Run the cached start | “This profile deploys the node and waits until Valkey answers its health check.” | Readiness |
| 00:27–00:50 | Run `make demo-standalone` | “Now Valkey answers PING, stores one value, returns it, and reports standalone mode with no replica.” | `PONG`, `SET`, `GET`, `INFO` |
| 00:50–01:00 | Hold `role:master` and `server_mode:standalone` | “One process owns the whole keyspace. It is simple, fast, and has no automatic failover.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "One writable Valkey node"
docker compose --profile valkey-standalone config |
  yq -C '.services.standalone |
    {"command": .command, "healthcheck": .healthcheck, "volumes": .volumes}'

make start PROFILE=valkey-standalone
make demo-standalone
```

## After recording

```shell
make stop
```

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] Startup reaches a healthy standalone node during the take.
- [ ] The reel shows `PONG`, the stored value, and `server_mode:standalone`.
- [ ] Cleanup removes the Compose project after recording.

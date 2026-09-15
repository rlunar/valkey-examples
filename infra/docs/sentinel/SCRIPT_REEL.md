# Sentinel-Managed Valkey Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: replication architecture, cached deployment, failover, takeaway
- Behavioral source: `make demo-sentinel`
- Runbook source: [`DEMO.md`](DEMO.md)

## Prepare off camera

Run from `infra/`:

```shell
make setup
make verify
make start PROFILE=valkey-sentinel
make stop
```

Start every take from a clean topology because the demo stops the original
primary.

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:06 | Title: “What happens when the Valkey primary stops?” | “Replication keeps a copy. Sentinel decides when that copy becomes the new primary.” | Hook |
| 00:06–00:15 | Show two data nodes and three Sentinels | “One primary replicates to one replica while three Sentinel processes monitor the named primary.” | Architecture |
| 00:15–00:28 | Run the cached start | “Compose deploys all five processes and waits for healthy data and discovery services.” | Readiness |
| 00:28–00:53 | Run `make demo-sentinel` | “The demo writes a value, waits for the replica, stops the primary, and polls until Sentinel promotes the replica.” | Replication and failover |
| 00:53–01:00 | Hold the promoted role and recovered value | “The address changed, the value survived, and the replica now reports `role:master`.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Two data nodes and three Sentinel voters"
docker compose --profile valkey-sentinel config --services

make start PROFILE=valkey-sentinel
make demo-sentinel
```

## After recording

```shell
make stop
```

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] The reel shows the initial primary and one acknowledged replica.
- [ ] The promoted service is `sentinel-replica:6379`.
- [ ] The recovered value is visible before the closing line.

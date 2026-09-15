# Valkey Cluster Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: three-primary architecture, cached deployment, slot proof, takeaway
- Behavioral source: `make demo-cluster`
- Runbook source: [`DEMO.md`](DEMO.md)

## Prepare off camera

Run from `infra/`:

```shell
make setup
make verify
make start PROFILE=valkey-cluster-3
make stop
```

The warm start caches the image and proves cluster initialization before the
recorded take.

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:05 | Title: “One keyspace, three Valkey primaries” | “Valkey Cluster splits one logical keyspace across numbered hash slots.” | Hook |
| 00:05–00:14 | Show the three nodes and initializer | “Three writable nodes start first. A one-shot initializer assigns all 16,384 slots.” | Architecture |
| 00:14–00:29 | Run the cached start | “Compose deploys the nodes, waits for health, and creates the cluster.” | Readiness |
| 00:29–00:51 | Run `make demo-cluster` | “A cluster-aware client follows slot ownership, stores one key, reads it back, and checks the slot map.” | Routed `SET` and `GET` |
| 00:51–01:00 | Hold `16384` slots and `3` primaries | “Every slot has an owner, and all three nodes are writable primaries.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Three primaries and one cluster initializer"
docker compose --profile valkey-cluster-3 config --services

make start PROFILE=valkey-cluster-3
make demo-cluster
```

## After recording

```shell
make stop
```

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] The cluster becomes healthy during the take.
- [ ] The output shows `cluster_state: ok`, `16384` slots, and three primaries.
- [ ] Cleanup removes the transient cluster membership state.

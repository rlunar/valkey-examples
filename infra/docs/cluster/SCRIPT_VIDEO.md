# Valkey Cluster Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 6–8 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo-cluster`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The primary build uses three primaries. The six-node deployment with replicas is
an optional chapter after the five-minute checkpoint.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Cache the pinned image before recording.

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:20 | Preview the final cluster proof | “You will deploy three Valkey primaries, assign every hash slot, and route one key to its owner.” | Finished result |
| 00:20–01:05 | Render the cluster architecture | “Cluster divides 16,384 slots across independent writable primaries. Clients use the slot map to find each key.” | Architecture |
| 01:05–02:05 | Display one node and `cluster-init-3` | “Each node enables cluster mode. The initializer waits for health and creates the slot map once.” | Effective Compose |
| 02:05–02:45 | Display the shared Valkey settings | “The nodes share memory and persistence defaults, while cluster membership stays in their command arguments.” | Configuration boundary |
| 02:45–03:35 | Run `make start PROFILE=valkey-cluster-3` | “Compose deploys three nodes and runs the one-shot cluster creation command.” | Healthy cluster |
| 03:35–04:35 | Run `make demo-cluster` | “The client follows redirections, proves the key round trip, and confirms complete slot coverage.” | Behavioral proof |
| 04:35–05:00 | Show the key slot and summarize | “The key maps deterministically to one slot. The three-primary build is complete.” | Five-minute checkpoint |
| 05:00–07:00 | Optional: deploy `valkey-cluster-6` | “Adding one replica per primary changes redundancy, not the number of shards.” | Optional variation |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Teaching profiles$/p' \
  docs/DESIGN.md |
  glow - --width 100

docker compose --profile valkey-cluster-3 config |
  yq -C '.services |
    with_entries(select(.key == "cluster-node-1" or .key == "cluster-init-3")) |
    map_values({"command": .command, "depends_on": .depends_on})'

bat --paging=never --style=numbers --highlight-line 20:35 \
  valkey/valkey.conf

make start PROFILE=valkey-cluster-3
make demo-cluster
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER KEYSLOT 'valkey-examples:infra:cluster:{demo}'
make stop
```

Optional chapter:

```shell
make start PROFILE=valkey-cluster-6
docker compose --profile valkey-cluster-6 exec -T cluster-node-1 \
  valkey-cli CLUSTER NODES
make stop
```

## Verification

- [ ] The three-primary cluster succeeds before 05:00.
- [ ] The six-node variation begins only after the primary checkpoint.
- [ ] The script distinguishes sharding from replication.
- [ ] Cleanup removes all nodes and transient slot maps.

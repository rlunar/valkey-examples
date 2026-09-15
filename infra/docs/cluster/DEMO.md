# Valkey Cluster Demo Runbook

## Observable goal

Show three writable primary nodes forming one healthy Valkey Cluster, covering
all 16,384 hash slots, and routing a key to the node that owns its slot.

Run every command from the `infra/` directory.

## Prepare

```shell
make setup
make verify
make start PROFILE=valkey-cluster-3
```

Confirm that the three nodes are healthy and cluster initialization completed:

```shell
docker compose --profile valkey-cluster-3 ps
docker compose --profile valkey-cluster-3 logs cluster-init-3
```

## Presentation path

### 1. Show the architecture and cluster commands

Render the architecture section from [`../DESIGN.md`](../DESIGN.md):

```shell
gum style --bold "Cluster architecture"
sed -n '/^## Architecture$/,/^## Teaching profiles$/p' \
  docs/DESIGN.md |
  glow - --width 100
```

Display the expanded command for one node and the one-shot cluster creation
service from [`../../compose.yaml`](../../compose.yaml):

```shell
gum style --bold "Cluster node and initialization commands"
docker compose --profile valkey-cluster-3 config |
  yq -C '.services |
    with_entries(
      select(.key == "cluster-node-1" or .key == "cluster-init-3")
    ) |
    map_values({
      "profiles": .profiles,
      "command": .command,
      "depends_on": .depends_on
    })'
```

Display the common settings that every cluster node loads:

```shell
gum style --bold "Shared Valkey configuration"
bat --paging=never --style=numbers valkey/valkey.conf
```

Focus on the cluster node arguments:

```text
--cluster-enabled yes
--cluster-config-file /data/nodes.conf
--cluster-preferred-endpoint-type hostname
```

The node command enables cluster mode. The `cluster-init-3` command waits for
three healthy nodes and assigns all 16,384 slots across them.

### 2. Run the prepared demo

```shell
make demo-cluster
```

Expected output:

```text
Deployment: cluster
Validation: cluster bootstrap node
Container: cluster-node-1 (running)
Transport: plaintext
PING: PONG
Key: valkey-examples:infra:cluster:{demo}
SET: OK
GET: cluster-demo
INFO server:
valkey_version:9.1.1
server_mode:cluster
tcp_port:6379
INFO memory:
maxmemory:268435456
maxmemory_policy:noeviction
INFO replication:
role:master
Cluster state: ok
Slots assigned: 16384
Primary nodes: 3
```

The target verifies that the bootstrap container is running, sends `PING`,
performs a cluster-routed `SET` and `GET`, displays selected `INFO` fields,
then inspects slot coverage and primary count.

### 3. Show the key's slot

```shell
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER KEYSLOT 'valkey-examples:infra:cluster:{demo}'
```

Then display the slot ranges:

```shell
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER SLOTS
```

Explain that the `{demo}` hash tag controls which substring is hashed. Keys
sharing that tag map to the same slot.

### 4. Clean up

```shell
make stop
```

## Video beat sheet

| Time | Visual | Narration | Evidence |
| --- | --- | --- | --- |
| 00:00 | Cluster architecture | Sharding divides one logical keyspace across primaries | Design diagram |
| 00:15 | Cluster creation command | Three nodes divide all hash slots | `cluster-init-3` |
| 00:30 | `make demo-cluster` | A cluster-aware client follows slot ownership | Healthy output |
| 00:50 | `CLUSTER KEYSLOT` and `CLUSTER SLOTS` | The key maps deterministically to one owner | Slot number and ranges |
| 01:10 | Cleanup | Nodes and transient slot maps are disposable | `make stop` |

## Recovery

If cluster state is not `ok`, recreate all three nodes and the slot map:

```shell
make stop
make start PROFILE=valkey-cluster-3
```

Inspect initialization and node logs:

```shell
docker compose --profile valkey-cluster-3 logs --tail=150 \
  cluster-init-3 cluster-node-1 cluster-node-2 cluster-node-3
```

## Pre-publication checklist

- [ ] Cluster state is `ok`.
- [ ] The bootstrap container reports `PONG`, a successful key round trip, and
  server, memory, and replication `INFO`.
- [ ] All 16,384 slots are assigned.
- [ ] Three primary nodes are reported.
- [ ] `make stop` removes all cluster services.

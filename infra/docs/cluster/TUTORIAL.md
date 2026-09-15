# Tutorial: Understand Valkey Cluster

## Read this first

A Valkey Cluster splits keys between several primary nodes. Each key belongs
to one of 16,384 numbered slots, and each primary owns a range of those slots.

Key words:

- **cluster:** Valkey nodes that work as one logical database;
- **slot:** the numbered group to which a key belongs;
- **shard:** the slots and data owned by one primary;
- **redirect:** a reply that tells the client to contact another node; and
- **replica:** a node that copies one primary's data.

Start with the three-node path. The six-node section adds replicas after the
sharding model is clear.

Cluster slots work like the Hogwarts Sorting Hat: Valkey assigns each key to
one shard. Unlike the hat, Valkey uses a repeatable calculation, so the same
key receives the same slot.

## Learning outcome

You will learn how three Valkey primaries form one sharded keyspace, assign all
16,384 hash slots, and redirect a cluster-aware client to the correct node.

You get the shared Valkey configuration and every Compose definition you need
for the three-node and six-node deployments. You do not need an external
configuration file to understand the topology.

## 1. Inspect the reusable cluster-node definition

Every cluster node first loads the complete shared
`infra/valkey/valkey.conf`:

<!-- BEGIN VERBATIM: infra/valkey/valkey.conf -->
```conf
# Shared local Valkey defaults for every plaintext infrastructure profile.
#
# Role-specific settings such as replicaof and cluster-enabled remain in
# compose.yaml. Keep this file focused on behavior that should be identical
# across standalone, replicated, Sentinel-managed, and clustered nodes.

bind 0.0.0.0
protected-mode no
port 6379

daemonize no
supervised no
loglevel notice

timeout 0
tcp-keepalive 300
tcp-backlog 511

databases 16
dir /data
save ""
appendonly no

# Keep local examples bounded without allowing silent data loss. Capsules that
# intentionally demonstrate cache eviction should provide a dedicated profile
# rather than changing this shared correctness-oriented default.
maxmemory 256mb
maxmemory-policy noeviction
maxmemory-samples 5
maxmemory-eviction-tenacity 10

# Valkey 9 threads both socket reads and writes when io-threads is greater than
# one. Two threads keep the local profile modest while exercising the setting.
io-threads 2

# Make cleanup and expiry work asynchronous where Valkey supports it.
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
replica-lazy-flush yes
lazyfree-lazy-user-del yes
lazyfree-lazy-user-flush yes
```
<!-- END VERBATIM: infra/valkey/valkey.conf -->

The following exact `infra/compose.yaml` anchors add the cluster-specific
settings:

```yaml
name: ${COMPOSE_PROJECT_NAME:-valkey-examples-infra}

x-valkey-image: &valkey-image
  image: ${VALKEY_IMAGE:-valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9}

x-valkey-container: &valkey-container
  <<: *valkey-image
  restart: "no"
  networks:
    - demo
  security_opt:
    - no-new-privileges:true

x-valkey: &valkey
  <<: *valkey-container
  command:
    - valkey-server
    - /etc/valkey/valkey.conf
  volumes:
    - ${INFRA_ROOT:-.}/valkey/valkey.conf:/etc/valkey/valkey.conf:ro
  healthcheck:
    test: ["CMD", "valkey-cli", "-h", "127.0.0.1", "-p", "6379", "ping"]
    interval: 1s
    timeout: 1s
    retries: 30
    start_period: 2s

x-cluster-node: &cluster-node
  <<: *valkey
  command:
    - /bin/sh
    - -c
    - >-
      exec valkey-server
      /etc/valkey/valkey.conf
      --cluster-enabled yes
      --cluster-config-file /data/nodes.conf
      --cluster-node-timeout 5000
      --cluster-announce-hostname "$${HOSTNAME}"
      --cluster-announce-port 6379
      --cluster-announce-bus-port 16379
      --cluster-preferred-endpoint-type hostname
  tmpfs:
    - /data
```

The command-line settings are:

```text
--cluster-enabled yes
--cluster-config-file /data/nodes.conf
--cluster-node-timeout 5000
--cluster-announce-hostname <container hostname>
```

The `nodes.conf` file holds node-local runtime state. Valkey stores it in
`tmpfs`, so each tutorial run starts without stale cluster membership.

## 2. Inspect cluster creation

These are the complete three-node service definitions. The `cluster-init-3`
one-shot service waits for all three nodes to become healthy, then creates the
cluster.

```yaml
services:
  cluster-node-1:
    <<: *cluster-node
    profiles: ["valkey-cluster-3", "valkey-cluster-6"]
    hostname: cluster-node-1

  cluster-node-2:
    <<: *cluster-node
    profiles: ["valkey-cluster-3", "valkey-cluster-6"]
    hostname: cluster-node-2

  cluster-node-3:
    <<: *cluster-node
    profiles: ["valkey-cluster-3", "valkey-cluster-6"]
    hostname: cluster-node-3

  cluster-init-3:
    <<: *valkey-image
    profiles: ["valkey-cluster-3"]
    restart: "no"
    command:
      - valkey-cli
      - --cluster
      - create
      - cluster-node-1:6379
      - cluster-node-2:6379
      - cluster-node-3:6379
      - --cluster-yes
    networks:
      - demo
    security_opt:
      - no-new-privileges:true
    depends_on:
      cluster-node-1:
        condition: service_healthy
      cluster-node-2:
        condition: service_healthy
      cluster-node-3:
        condition: service_healthy

networks:
  demo:
    driver: bridge
```

With no `--cluster-replicas` argument, all three nodes become primaries and
divide the slot space.

Checkpoint:

```shell
docker compose --profile valkey-cluster-3 config --services
```

## 3. Start and verify the slot map

```shell
make start PROFILE=valkey-cluster-3
```

Query cluster health:

```shell
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER INFO
```

Checkpoint: find `cluster_state:ok` and
`cluster_slots_assigned:16384`.

List membership:

```shell
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER NODES
```

Three lines carry the `master` flag.

## 4. Observe client routing

Run:

```shell
make demo-cluster
```

Before inspecting cluster state, the script confirms that
`cluster-node-1` is running and executes:

```text
PING
SET valkey-examples:infra:cluster:{demo} cluster-demo
GET valkey-examples:infra:cluster:{demo}
INFO server
INFO memory
INFO replication
```

The output must show `PING: PONG`, `SET: OK`, `GET: cluster-demo`,
`server_mode:cluster`, the shared memory policy, and `role:master`.

The validator uses `valkey-cli -c`. The `-c` option follows `MOVED` replies
when the bootstrap node does not own the key's slot.

Compare the key's slot with the cluster ranges:

```shell
docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER KEYSLOT 'valkey-examples:infra:cluster:{demo}'

docker compose --profile valkey-cluster-3 exec -T cluster-node-1 \
  valkey-cli CLUSTER SLOTS
```

The braces are a hash tag. Only `demo` is hashed, allowing related keys with
the same tag to share a slot when a multi-key command requires it.

## 5. Add redundancy without changing sharding

The first three node definitions already include the `valkey-cluster-6`
profile. The exact additional node and initializer definitions are:

```yaml
cluster-node-4:
  <<: *cluster-node
  profiles: ["valkey-cluster-6"]
  hostname: cluster-node-4

cluster-node-5:
  <<: *cluster-node
  profiles: ["valkey-cluster-6"]
  hostname: cluster-node-5

cluster-node-6:
  <<: *cluster-node
  profiles: ["valkey-cluster-6"]
  hostname: cluster-node-6

cluster-init-6:
  <<: *valkey-image
  profiles: ["valkey-cluster-6"]
  restart: "no"
  command:
    - valkey-cli
    - --cluster
    - create
    - cluster-node-1:6379
    - cluster-node-2:6379
    - cluster-node-3:6379
    - cluster-node-4:6379
    - cluster-node-5:6379
    - cluster-node-6:6379
    - --cluster-replicas
    - "1"
    - --cluster-yes
  networks:
    - demo
  security_opt:
    - no-new-privileges:true
  depends_on:
    cluster-node-1:
      condition: service_healthy
    cluster-node-2:
      condition: service_healthy
    cluster-node-3:
      condition: service_healthy
    cluster-node-4:
      condition: service_healthy
    cluster-node-5:
      condition: service_healthy
    cluster-node-6:
      condition: service_healthy
```

This still produces three primary shards, but each primary receives one
replica. It changes failure tolerance, not the number of independent slot
owners.

Try the larger profile after stopping the three-node cluster:

```shell
make stop
make start PROFILE=valkey-cluster-6

docker compose --profile valkey-cluster-6 exec -T cluster-node-1 \
  valkey-cli CLUSTER NODES
```

The output contains three primaries and three replicas.

## Final cleanup

```shell
make stop
```

## Final takeaway

Valkey Cluster shards one logical keyspace by hash slot; cluster-aware clients
use the slot map and redirections to reach the primary that owns each key.

# Tutorial: Understand Sentinel-Managed Replication

## Read this first

This deployment has two data nodes and three Sentinel processes. The primary
accepts writes. The replica copies the data. Sentinel watches both nodes and
can promote the replica if the primary stops.

Key words:

- **replication:** copying data from a primary to a replica;
- **Sentinel:** a process that watches Valkey nodes;
- **quorum:** the number of Sentinels that must agree;
- **promotion:** changing a replica into the new primary; and
- **discovery:** asking Sentinel where the primary is now.

Use the included configuration as a reference. Follow the numbered checkpoints
first, then return to individual settings when you need them.

Think of Sentinel as Mission Control: several processes watch the primary,
agree when it has failed, and coordinate a replacement.

## Learning outcome

You will learn the separate jobs of Valkey replication and Sentinel.
Replication copies data, while Sentinel monitors, elects, and reports the
current primary.

You get the complete shared Valkey and Sentinel configuration, plus every
Compose definition you need for this topology. You do not need an external
file to understand the deployment.

## 1. Identify the five processes

These exact definitions from `infra/compose.yaml` create the five processes:

- `sentinel-primary` is the initial writable data node;
- `sentinel-replica` starts with `--replicaof sentinel-primary 6379`; and
- three Sentinel processes load the same monitored-primary configuration.

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

x-ephemeral-valkey: &ephemeral-valkey
  <<: *valkey
  tmpfs:
    - /data

x-sentinel: &sentinel
  <<: *valkey-container
  profiles: ["valkey-sentinel"]
  command:
    - /bin/sh
    - -c
    - cp /etc/valkey/sentinel.conf /tmp/sentinel.conf && exec valkey-sentinel /tmp/sentinel.conf
  volumes:
    - ${INFRA_ROOT:-.}/sentinel/sentinel.conf:/etc/valkey/sentinel.conf:ro
  tmpfs:
    - /tmp
  healthcheck:
    test: ["CMD", "valkey-cli", "-h", "127.0.0.1", "-p", "26379", "ping"]
    interval: 1s
    timeout: 1s
    retries: 30
    start_period: 2s
  depends_on:
    sentinel-primary:
      condition: service_healthy
    sentinel-replica:
      condition: service_healthy

services:
  sentinel-primary:
    <<: *ephemeral-valkey
    profiles: ["valkey-sentinel"]

  sentinel-replica:
    <<: *ephemeral-valkey
    profiles: ["valkey-sentinel"]
    command:
      - valkey-server
      - /etc/valkey/valkey.conf
      - --replicaof
      - sentinel-primary
      - "6379"
    depends_on:
      sentinel-primary:
        condition: service_healthy

  sentinel-1:
    <<: *sentinel

  sentinel-2:
    <<: *sentinel

  sentinel-3:
    <<: *sentinel

networks:
  demo:
    driver: bridge
```

Checkpoint:

```shell
docker compose --profile valkey-sentinel config --services
```

The output contains the two data nodes and all three Sentinels.

## 2. Understand the Sentinel configuration

Both data nodes load the complete shared `infra/valkey/valkey.conf`:

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

Replication is added only to `sentinel-replica` through the Compose command,
so the shared file remains role-neutral.

Each Sentinel process receives a writable temporary copy of this complete
`infra/sentinel/sentinel.conf`:

<!-- BEGIN VERBATIM: infra/sentinel/sentinel.conf -->
```conf
port 26379
bind 0.0.0.0
protected-mode no
dir /tmp

sentinel resolve-hostnames yes
sentinel announce-hostnames yes
sentinel monitor demo-primary sentinel-primary 6379 2
sentinel down-after-milliseconds demo-primary 1500
sentinel failover-timeout demo-primary 10000
sentinel parallel-syncs demo-primary 1
```
<!-- END VERBATIM: infra/sentinel/sentinel.conf -->

`demo-primary` is the logical name clients discover. The hostname after it is
only the initial primary. Sentinel may later map the same logical name to a
different host.

## 3. Start and query discovery

```shell
make start PROFILE=valkey-sentinel
```

Ask one Sentinel for the current primary:

```shell
docker compose --profile valkey-sentinel exec -T sentinel-1 \
  valkey-cli --raw -p 26379 \
  SENTINEL get-master-addr-by-name demo-primary
```

Expected result:

```text
sentinel-primary
6379
```

Checkpoint: query `sentinel-2` and confirm it reports the same address.

## 4. Validate the primary and prove replication

The prepared demo first calls the shared validator against
`sentinel-primary`. It checks that the container is running and executes:

```text
PING
SET valkey-examples:infra:sentinel before-failover
GET valkey-examples:infra:sentinel
INFO server
INFO memory
INFO replication
```

The output must show `Container: sentinel-primary (running)`, `PING: PONG`,
`SET: OK`, `GET: before-failover`, and `role:master`. It also displays the
pinned server version, memory limit, and eviction policy.

Run the complete path:

```shell
make demo-sentinel
```

After the round trip, the demo runs `WAIT 1 5000`. The result must be `1`,
which makes the later failover read a bounded proof of replication rather than
a timing assumption.

## 5. Trigger and observe failover

Sentinel first marks the original primary subjectively and objectively down,
then the quorum elects a leader and promotes the replica.

After promotion:

```shell
docker compose --profile valkey-sentinel exec -T sentinel-1 \
  valkey-cli --raw -p 26379 \
  SENTINEL get-master-addr-by-name demo-primary
```

The logical name now resolves to the promoted replica's container-network
address on port `6379`. Docker may present that address as an ephemeral IP.
The demo confirms the stable service identity by displaying:

```text
Promoted primary: sentinel-replica:6379
Promoted INFO replication:
role:master
GET after failover: before-failover
```

## 6. Separate client discovery from data commands

A Sentinel-aware client does not treat port `26379` as the data endpoint. It:

1. asks one or more Sentinels for `demo-primary`;
2. opens the data connection to the returned host and port; and
3. rediscovers after a relevant connection or role failure.

The infrastructure demo uses `valkey-cli` to make these two interactions
visible. Application capsules may hide them behind a topology-aware client
adapter.

## Final cleanup

```shell
make stop
```

## Final takeaway

Replication creates the recoverable copy; Sentinel turns that copy into an
automatically discoverable replacement primary after a quorum-backed election.

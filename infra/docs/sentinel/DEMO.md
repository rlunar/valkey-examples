# Sentinel-Managed Valkey Demo Runbook

## Observable goal

Show a primary replicating to one replica, three Sentinel processes reporting
the current primary, and automatic promotion after the original primary stops.

The failover is the demo's observable behavior. Run every command from the
`infra/` directory and start from a clean deployment.

## Prepare

```shell
make setup
make verify
make stop
make start PROFILE=valkey-sentinel
```

Confirm that two data nodes and three Sentinels are healthy:

```shell
docker compose --profile valkey-sentinel ps
```

## Presentation path

### 1. Show the architecture and five services

Render the architecture section from [`../DESIGN.md`](../DESIGN.md):

```shell
gum style --bold "Sentinel architecture"
sed -n '/^## Architecture$/,/^## Teaching profiles$/p' \
  docs/DESIGN.md |
  glow - --width 100
```

Display the commands and startup dependencies for the two data nodes and three
Sentinel processes from [`../../compose.yaml`](../../compose.yaml):

```shell
gum style --bold "Sentinel Compose services"
docker compose --profile valkey-sentinel config |
  yq -C '.services |
    with_entries(
      select(.key == "sentinel-primary" or
             .key == "sentinel-replica" or
             .key == "sentinel-1" or
             .key == "sentinel-2" or
             .key == "sentinel-3")
    ) |
    map_values({
      "profiles": .profiles,
      "command": .command,
      "depends_on": .depends_on
    })'
```

Display the complete monitored-primary configuration from
[`../../sentinel/sentinel.conf`](../../sentinel/sentinel.conf):

```shell
gum style --bold "Sentinel voting and timing"
bat --paging=never --style=numbers sentinel/sentinel.conf
```

Focus on:

```text
sentinel monitor demo-primary sentinel-primary 6379 2
```

The replica command identifies `sentinel-primary` as its source. The monitor
line gives that primary the logical name `demo-primary`. The final number is
the quorum, so two of the three Sentinels must agree that the primary is
unavailable.

### 2. Run the failover demo

```shell
make demo-sentinel
```

Expected output:

```text
Deployment: sentinel
Validation: Sentinel primary
Container: sentinel-primary (running)
Transport: plaintext
PING: PONG
Key: valkey-examples:infra:sentinel
SET: OK
GET: before-failover
INFO server:
valkey_version:9.1.1
server_mode:standalone
tcp_port:6379
INFO memory:
maxmemory:268435456
maxmemory_policy:noeviction
INFO replication:
role:master
Initial primary: sentinel-primary:6379
Replicas acknowledged: 1
Stopping sentinel-primary to trigger failover.
Promoted primary: sentinel-replica:6379
Promoted INFO replication:
role:master
GET after failover: before-failover
```

The target first verifies that the primary container is running, sends `PING`,
performs a `SET` and `GET`, and displays selected `INFO` fields. It then uses
`WAIT 1 5000` to prove the replica acknowledged the write, stops the original
primary, polls Sentinel for the promoted address, displays the promoted role,
and reads the value from the promoted node.

### 3. Show the new role

```shell
docker compose --profile valkey-sentinel exec -T sentinel-replica \
  valkey-cli INFO replication
```

Highlight `role:master`.

### 4. Clean up

```shell
make stop
```

## Video beat sheet

| Time | Visual | Narration | Evidence |
| --- | --- | --- | --- |
| 00:00 | Sentinel architecture | Replication preserves a copy; Sentinel manages discovery and election | Design diagram |
| 00:15 | `sentinel.conf` | Three voters monitor one named primary | Quorum setting |
| 00:30 | `make demo-sentinel` | An acknowledged write precedes failure | Initial output |
| 00:50 | Promotion output | The replica becomes the writable primary | New address and recovered value |
| 01:10 | Cleanup | Repeat from a clean topology | `make stop` |

## Recovery

The demo is intentionally not repeatable against the same running topology,
because the original primary has been stopped and the replica promoted.
Recreate it before another take:

```shell
make stop
make start PROFILE=valkey-sentinel
```

Inspect election details:

```shell
docker compose --profile valkey-sentinel logs --tail=150 \
  sentinel-1 sentinel-2 sentinel-3
```

## Pre-publication checklist

- [ ] The initial primary is `sentinel-primary:6379`.
- [ ] The initial container reports `PONG`, a successful key round trip, and
  server, memory, and replication `INFO`.
- [ ] One replica acknowledges the write.
- [ ] Sentinel promotes `sentinel-replica:6379`.
- [ ] The promoted node reports `role:master` and returns `before-failover`.
- [ ] `make stop` removes the failed and promoted topology.

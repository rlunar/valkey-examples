# Standalone Valkey Demo Runbook

## Observable goal

Show that one Valkey process is running, accepts commands, applies the shared
runtime configuration, and stores a value without replication or sharding.
Then validate the same standalone behavior through plaintext and mutual-TLS
host profiles.

Run every command from the `infra/` directory.

## Prepare

```shell
make setup
make verify
make start PROFILE=valkey-standalone
```

Confirm that the standalone service is healthy:

```shell
docker compose --profile valkey-standalone ps standalone
```

## Presentation path

### 1. Show the architecture and configuration

Render the architecture section from [`../DESIGN.md`](../DESIGN.md):

```shell
gum style --bold "Standalone architecture"
sed -n '/^## Architecture$/,/^## Teaching profiles$/p' \
  docs/DESIGN.md |
  glow - --width 100
```

Display the expanded standalone service from
[`../../compose.yaml`](../../compose.yaml):

```shell
gum style --bold "Standalone Compose service"
docker compose --profile valkey-standalone config |
  yq -C '{
    "profiles": .services.standalone.profiles,
    "command": .services.standalone.command,
    "healthcheck": .services.standalone.healthcheck,
    "volumes": .services.standalone.volumes
  }'
```

Display the complete shared configuration from
[`../../valkey/valkey.conf`](../../valkey/valkey.conf):

```shell
gum style --bold "Shared Valkey configuration"
bat --paging=never --style=numbers valkey/valkey.conf
```

Point out `io-threads`, `maxmemory`, `maxmemory-policy`, and the lazy-freeing
settings. The Compose output shows that the standalone service mounts this
file and starts one Valkey process.

Before the TLS portion, display the TLS service and its small configuration
overlay:

```shell
gum style --bold "Mutual-TLS overlay"
docker compose --profile valkey-standalone-tls-host config |
  yq -C '{
    "command": .services."valkey-tls".command,
    "ports": .services."valkey-tls".ports,
    "healthcheck": .services."valkey-tls".healthcheck,
    "volumes": .services."valkey-tls".volumes
  }'
bat --paging=never --style=numbers valkey/valkey-tls.conf
```

Suggested narration:

> This deployment has one data node. There is no replica, election layer, or
> hash-slot map, so every command reaches the same writable process.

### 2. Run the prepared demo

```shell
make demo-standalone
```

Expected output:

```text
Deployment: standalone
Validation: standalone topology
Container: standalone (running)
Transport: plaintext
PING: PONG
Key: valkey-examples:infra:standalone
SET: OK
GET: standalone-demo
INFO server:
valkey_version:9.1.1
server_mode:standalone
tcp_port:6379
INFO memory:
maxmemory:268435456
maxmemory_policy:noeviction
INFO replication:
role:master
```

The target verifies that the container is running, sends `PING`, performs a
`SET` and `GET` round trip, and displays selected fields from `INFO server`,
`INFO memory`, and `INFO replication`.

### 3. Validate the plaintext host profile

```shell
make stop
make start PROFILE=valkey-standalone-host
make validate-plaintext
```

Expected output:

```text
Validation: plaintext host profile
Container: valkey (running)
Transport: plaintext
PING: PONG
Key: valkey-examples:infra:plaintext
SET: OK
GET: plaintext-demo
INFO server:
valkey_version:9.1.1
server_mode:standalone
tcp_port:6379
INFO memory:
maxmemory:268435456
maxmemory_policy:noeviction
INFO replication:
role:master
```

This profile publishes Valkey only on the loopback interface for host-based
example applications. The validation itself runs inside the container so the
same commands work when a host port is overridden.

### 4. Validate the mutual-TLS host profile

```shell
make stop
make start PROFILE=valkey-standalone-tls-host
make validate-tls
```

Expected output:

```text
Validation: mutual TLS host profile
Container: valkey-tls (running)
Transport: mutual TLS
PING: PONG
Key: valkey-examples:infra:tls
SET: OK
GET: tls-demo
INFO server:
valkey_version:9.1.1
server_mode:standalone
tcp_port:6379
INFO memory:
maxmemory:268435456
maxmemory_policy:noeviction
INFO replication:
role:master
```

The TLS validator supplies the local CA, client certificate, and client key to
every command. A successful `PING` alone would prove only connectivity; the
key round trip and `INFO` output also prove authenticated command execution and
the expected server configuration.

### 5. Clean up

```shell
make stop
make tls-clean
```

## Video beat sheet

| Time | Visual | Narration | Evidence |
| --- | --- | --- | --- |
| 00:00 | Architecture branch in [`../DESIGN.md`](../DESIGN.md) | One process owns the full keyspace | Standalone diagram |
| 00:10 | `compose.yaml` and `valkey.conf` | Role-specific Compose plus shared tuning | Service and config |
| 00:25 | `make demo-standalone` | Check the container, commands, and server state | PING, SET/GET, and INFO |
| 00:45 | Plaintext and TLS validation | The transport changes; the data behavior remains | Two validation targets |
| 01:10 | Cleanup | The deployment and generated certificates are disposable | `make stop` and `make tls-clean` |

## Recovery

If the demo says the service is not running:

```shell
make stop
make start PROFILE=valkey-standalone
```

Inspect only this project's logs:

```shell
docker compose --profile valkey-standalone logs --tail=100 standalone
```

## Pre-publication checklist

- [ ] `make verify` passes.
- [ ] Plaintext and TLS outputs report their containers as running.
- [ ] Both transports return `PONG`, `OK`, and the expected stored value.
- [ ] Both transports display server, memory, and replication `INFO` fields.
- [ ] `make stop` leaves no infrastructure containers running.
- [ ] `make tls-clean` removes generated local certificates.

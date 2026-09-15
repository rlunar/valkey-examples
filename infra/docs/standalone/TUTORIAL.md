# Tutorial: Understand the Standalone Deployment

## Read this first

A standalone deployment is one Valkey server. Every key and every command goes
to that one process.

Key words:

- **node:** one running Valkey server;
- **keyspace:** all keys stored by that server;
- **primary:** a node that accepts writes; and
- **TLS:** encryption and certificate checks for network traffic.

Read the explanation before the large configuration blocks. This tutorial
includes the configuration so you have all required context. You do not need
to memorize every line.

## Learning outcome

You will build a mental model of the smallest Valkey deployment. One process
owns the entire keyspace, accepts writes, and has no automatic failover.

This tutorial reproduces the configuration it explains. You do not need to
open `compose.yaml`, `valkey.conf`, or `valkey-tls.conf` to understand or
present the deployment.

## 1. Find the common node definition

You will use these exact standalone definitions from `infra/compose.yaml`.
The `x-valkey` anchor defines the image, command, mounted configuration,
network, security options, and health check reused by every data node. The
standalone service adds only its profile.

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

services:
  standalone:
    <<: *ephemeral-valkey
    profiles: ["valkey-standalone"]

networks:
  demo:
    driver: bridge
```

Checkpoint:

```shell
docker compose --profile valkey-standalone config --services
```

Expected service:

```text
standalone
```

## 2. Inspect the shared Valkey behavior

You can read the complete shared `infra/valkey/valkey.conf` below. Notice that
it contains common runtime behavior, but no `replicaof` or cluster directives.

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

Start the deployment:

```shell
make start PROFILE=valkey-standalone
```

Query the live configuration:

```shell
docker compose --profile valkey-standalone exec -T standalone \
  valkey-cli CONFIG GET io-threads maxmemory maxmemory-policy
```

Checkpoint: the node reports two I/O threads, 256 MiB of maximum memory, and
the `noeviction` policy.

## 3. Prove the node owns reads and writes

Run:

```shell
make demo-standalone
```

The script performs:

```text
verify the standalone container is running
PING
SET valkey-examples:infra:standalone standalone-demo
GET valkey-examples:infra:standalone
INFO server
INFO memory
INFO replication
```

The output must show:

- `Container: standalone (running)`;
- `PING: PONG`;
- `SET: OK` and `GET: standalone-demo`;
- the pinned Valkey version and standalone server mode;
- `maxmemory:268435456` and `maxmemory_policy:noeviction`; and
- `role:master`.

In Valkey terminology a writable standalone node still has the primary role,
even when it has no replicas.

## 4. Identify the tradeoff

Stop the process:

```shell
docker compose --profile valkey-standalone stop standalone
```

There is no second node to promote and no discovery layer to return another
address. This simplicity is useful for local development and workloads that
accept the availability boundary, but it is not automatic high availability.

Restart from a clean state:

```shell
make stop
make start PROFILE=valkey-standalone
make demo-standalone
```

## 5. Validate plaintext host access

The host-published plaintext profile uses this exact service definition:

```yaml
valkey:
  <<: *ephemeral-valkey
  profiles: ["valkey-standalone-host"]
  labels:
    io.valkey.examples.capsule: ${CAPSULE_ID:-shared-infra}
  ports:
    - "127.0.0.1:${VALKEY_PORT:-6379}:6379"
```

The `127.0.0.1` binding keeps the unauthenticated educational node off
non-loopback interfaces.

Start the loopback-published plaintext profile:

```shell
make stop
make start PROFILE=valkey-standalone-host
make validate-plaintext
```

`make validate-plaintext` confirms that the `valkey` container is running,
then performs `PING`, `SET`, `GET`, and selected `INFO` queries over plaintext.
The stored value must be `plaintext-demo`.

## 6. Validate mutual TLS

The TLS service mounts the shared configuration, a TLS overlay, and generated
CA, server, and client material:

```yaml
valkey-tls:
  <<: *valkey-container
  profiles: ["valkey-standalone-tls-host"]
  command:
    - valkey-server
    - /etc/valkey/valkey-tls.conf
  volumes:
    - ${INFRA_ROOT:-.}/valkey/valkey.conf:/etc/valkey/valkey.conf:ro
    - ${INFRA_ROOT:-.}/valkey/valkey-tls.conf:/etc/valkey/valkey-tls.conf:ro
    - ${TLS_CERT_DIR:-./.cache/tls}/ca.crt:/tls/ca.crt:ro
    - ${TLS_CERT_DIR:-./.cache/tls}/client.crt:/tls/client.crt:ro
    - ${TLS_CERT_DIR:-./.cache/tls}/client.key:/tls/client.key:ro
    - ${TLS_CERT_DIR:-./.cache/tls}/server.crt:/tls/server.crt:ro
    - ${TLS_CERT_DIR:-./.cache/tls}/server.key:/tls/server.key:ro
  tmpfs:
    - /data
  labels:
    io.valkey.examples.capsule: ${CAPSULE_ID:-shared-infra}
  ports:
    - "127.0.0.1:${VALKEY_TLS_PORT:-6380}:6379"
  healthcheck:
    test:
      - CMD
      - valkey-cli
      - --tls
      - --cacert
      - /tls/ca.crt
      - --cert
      - /tls/client.crt
      - --key
      - /tls/client.key
      - -h
      - 127.0.0.1
      - -p
      - "6379"
      - ping
    interval: 1s
    timeout: 2s
    retries: 30
    start_period: 2s
```

The complete `infra/valkey/valkey-tls.conf` overlay is:

<!-- BEGIN VERBATIM: infra/valkey/valkey-tls.conf -->
```conf
# TLS overlay for the opt-in standalone mutual-TLS profile.

include /etc/valkey/valkey.conf

port 0
tls-port 6379
tls-cert-file /tls/server.crt
tls-key-file /tls/server.key
tls-ca-cert-file /tls/ca.crt
tls-auth-clients yes
tls-protocols "TLSv1.2 TLSv1.3"
tls-prefer-server-ciphers yes
```
<!-- END VERBATIM: infra/valkey/valkey-tls.conf -->

`port 0` disables plaintext, `tls-auth-clients yes` requires a trusted client
certificate, and the protocol list permits TLS 1.2 and TLS 1.3.

Switch to the TLS-only profile:

```shell
make stop
make start PROFILE=valkey-standalone-tls-host
make validate-tls
```

Starting the profile generates an ignored local CA plus server and client
certificates. The validator connects with:

```text
--tls
--cacert /tls/ca.crt
--cert /tls/client.crt
--key /tls/client.key
```

The output confirms that `valkey-tls` is running, `PING` returns `PONG`, the
`SET` and `GET` round trip returns `tls-demo`, and the same `INFO` fields are
available through the authenticated connection.

The plaintext and TLS profiles preserve the same one-node data model. TLS
changes transport authentication and encryption, not availability or
sharding.

## Final cleanup

```shell
make stop
make tls-clean
```

## Final takeaway

A standalone deployment is one writable Valkey node with the smallest
operational surface and no built-in failover or horizontal sharding.

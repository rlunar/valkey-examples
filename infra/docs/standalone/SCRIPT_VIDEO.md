# Standalone Valkey Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 5–7 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo-standalone`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The primary build covers the private one-node profile. Plaintext host access and
mutual TLS are optional chapters after the five-minute checkpoint.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Cache the pinned Valkey image before recording.

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:20 | Preview the final `make demo-standalone` output | “You will deploy one Valkey node, prove a key round trip, and identify the availability tradeoff.” | Finished result |
| 00:20–01:00 | Render the standalone branch of `docs/DESIGN.md` | “The Make interface selects a Compose profile. That profile starts one private node using the shared Valkey configuration.” | Architecture |
| 01:00–02:00 | Query the resolved Compose service | “The service mounts one configuration file, stores disposable data in memory, and exposes a health check instead of a fixed sleep.” | Effective Compose |
| 02:00–02:45 | Display focused settings from `valkey.conf` | “The demo bounds memory, uses no eviction, and disables persistence because this data is disposable.” | Runtime settings |
| 02:45–03:30 | Run `make start PROFILE=valkey-standalone` | “Compose deploys the node and waits for PING to succeed.” | Healthy container |
| 03:30–04:30 | Run `make demo-standalone` | “The shared validator performs PING, SET, GET, and selected INFO queries against real Valkey.” | Behavioral proof |
| 04:30–05:00 | Stop the node and summarize | “The node is writable, but there is no replica or election layer. The primary build is complete.” | Cleanup and checkpoint |
| 05:00–06:30 | Optional: compare plaintext and mutual-TLS host profiles | “Transport security changes how clients connect; it does not add replication or sharding.” | Optional variation |

## Exact recording commands

```shell
sed -n '/^## Plain-language map$/,/^## Stable interface$/p' \
  docs/DESIGN.md |
  glow - --width 90

docker compose --profile valkey-standalone config |
  yq -C '.services.standalone |
    {"command": .command, "healthcheck": .healthcheck, "tmpfs": .tmpfs}'

bat --paging=never --style=numbers --highlight-line 20:35 \
  valkey/valkey.conf

make start PROFILE=valkey-standalone
make demo-standalone
make stop
```

Optional chapter:

```shell
make start PROFILE=valkey-standalone-host
make validate-plaintext
make stop

make start PROFILE=valkey-standalone-tls-host
make validate-tls
make stop
make tls-clean
```

## Verification

- [ ] `make demo-standalone` succeeds before 05:00.
- [ ] TLS appears only after the primary checkpoint.
- [ ] The narration distinguishes transport security from availability.
- [ ] Final cleanup removes containers and generated certificates.

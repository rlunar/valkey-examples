# Sentinel-Managed Valkey Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 6–8 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo-sentinel`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The primary build is complete when a clean topology promotes the replica and
reads the acknowledged value after failover.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Cache the pinned image and confirm no old Sentinel topology remains.

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:25 | Preview the promotion output | “You will deploy replication plus Sentinel, stop the primary, and recover the same value from the promoted replica.” | Finished result |
| 00:25–01:10 | Render the Sentinel architecture | “Replication copies data. Sentinel provides monitoring, quorum, discovery, and promotion.” | Architecture |
| 01:10–02:10 | Display the five resolved services | “Two processes hold data. Three independent Sentinel voters share the monitored-primary configuration.” | Effective Compose |
| 02:10–02:50 | Display `sentinel.conf` | “Two voters form quorum. A short local timeout makes the failure visible during the tutorial.” | Quorum and timing |
| 02:50–03:35 | Run `make start PROFILE=valkey-sentinel` | “Compose starts the primary, waits for the replica, then starts the three Sentinel processes.” | Healthy topology |
| 03:35–04:45 | Run `make demo-sentinel` | “The demo writes, waits for one replica acknowledgement, stops the primary, observes promotion, and reads the original value.” | Real failover |
| 04:45–05:00 | Hold the new role | “The primary changed without changing the logical Sentinel name. The primary build is complete.” | Five-minute checkpoint |
| 05:00–07:00 | Explain discovery versus data connections | “Clients ask Sentinel where the primary is, then send data commands to the returned Valkey endpoint.” | Deeper explanation |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Teaching profiles$/p' \
  docs/DESIGN.md |
  glow - --width 100

docker compose --profile valkey-sentinel config |
  yq -C '.services |
    with_entries(select(.key | test("^sentinel-(primary|replica|[123])$"))) |
    map_values({"command": .command, "depends_on": .depends_on})'

bat --paging=never --style=numbers sentinel/sentinel.conf

make start PROFILE=valkey-sentinel
make demo-sentinel
make stop
```

## Verification

- [ ] Promotion and recovered read complete before 05:00.
- [ ] The script explains replication separately from Sentinel.
- [ ] The take starts from a clean topology.
- [ ] Cleanup removes both data nodes and all three Sentinels.

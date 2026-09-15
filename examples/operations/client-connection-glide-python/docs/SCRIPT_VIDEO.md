# Minimal Valkey GLIDE Python Connection Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 5–6 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The standalone build completes before five minutes. Cluster is an optional
comparison afterward.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Use prepared files from the tutorial rather than filming repetitive typing.

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:20 | Preview `hello from GLIDE` | “You will connect Python to Valkey, store one string, retrieve it, and close the client.” | Finished result |
| 00:20–00:55 | Render the architecture | “The application loads three environment values, creates a GLIDE client, and sends commands to one selected topology.” | Architecture |
| 00:55–01:35 | Show `.env` | “The mode and seed addresses are configuration. The application code stays the same.” | Configuration |
| 01:35–02:55 | Walk through `app.py` | “The constructor selects the normal or cluster client. The command path is still SET, GET, decode, print, and close.” | Core implementation |
| 02:55–03:40 | Show the app-only Compose service and shared profile | “The capsule owns its application image. The root infrastructure capsule owns Valkey.” | Runtime boundary |
| 03:40–04:20 | Run `make start` | “The cached standalone profile becomes healthy.” | Readiness |
| 04:20–04:50 | Run `make demo` | “The real process writes and reads the configured message.” | Behavioral proof |
| 04:50–05:00 | Run cleanup | “The standalone build is complete.” | Five-minute checkpoint |
| 05:00–06:00 | Optional: switch `.env` to cluster and repeat | “Only client construction changes; SET and GET do not.” | Topology comparison |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Responsibilities$/p' \
  docs/DESIGN.md |
  glow - --width 90

bat --paging=never --style=numbers .env
bat --paging=never --style=numbers \
  --highlight-line 23:43 \
  --highlight-line 52:59 \
  src/valkey_connection/app.py

bash -c 'source scripts/common.sh; compose config' |
  yq -C '.services.app | {"build": .build, "environment": .environment}'

make start
make demo
make reset
make stop
```

Optional cluster chapter:

```shell
export VALKEY_MODE=cluster
export VALKEY_ADDRESSES=cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
make start
make demo
make stop
unset VALKEY_MODE VALKEY_ADDRESSES
```

## Verification

- [ ] Standalone prints `hello from GLIDE` before 05:00.
- [ ] Cluster begins only after the primary checkpoint.
- [ ] The video shows the constructor and the visible `SET`/`GET`.
- [ ] Cleanup removes resources and clears the temporary environment overrides.

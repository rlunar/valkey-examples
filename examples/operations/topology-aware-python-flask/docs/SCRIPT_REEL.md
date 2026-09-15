# Topology-Aware Flask Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: adapter architecture, one cached topology, counter proof
- Behavioral source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)

Use standalone for the primary reel. Record Sentinel and cluster as separate
takes.

## Prepare off camera

```shell
cp -n .env.example .env
make setup
make verify
TOPOLOGY=standalone make start
TOPOLOGY=standalone make stop
```

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:06 | Title: “One Flask app, three Valkey topologies” | “The routes never need to know whether Valkey is standalone, Sentinel-managed, or clustered.” | Hook |
| 00:06–00:18 | Show `CounterStore` and `ValkeyStore` | “Flask calls one store interface. `ValkeyStore` owns client construction and topology-specific discovery.” | Architecture |
| 00:18–00:35 | Run standalone startup | “This take deploys the cached standalone profile and waits for Flask and Valkey.” | Readiness |
| 00:35–00:54 | Run the journey | “The application reports the topology, increments the same counter twice, and reads the stored value.” | `1 -> 2`, stored `2` |
| 00:54–01:00 | Hold the topology and client type | “Change the adapter, not the route.” | Takeaway |

## Exact recording commands

```shell
gum style --bold "Routes depend on CounterStore"
bat --paging=never --style=numbers \
  --highlight-line 111:145 \
  src/valkey_flask_demo/app.py
bat --paging=never --style=numbers \
  --highlight-line 31:88 \
  src/valkey_flask_demo/store.py

TOPOLOGY=standalone make start
TOPOLOGY=standalone make demo
```

## After recording

```shell
TOPOLOGY=standalone make reset
TOPOLOGY=standalone make stop
```

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] The take uses one topology only.
- [ ] The counter visibly changes from `1` to `2`.
- [ ] The narration identifies the store as the topology boundary.

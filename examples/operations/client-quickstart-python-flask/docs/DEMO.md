# Valkey GLIDE Flask Quickstart Runbook

## 60-second goal

Show this path:

1. `app.py` creates one `ValkeyClient`;
2. the route calls `valkey.client.set(...)`;
3. the route calls `valkey.client.get(...)`; and
4. the same code runs against standalone or cluster Valkey.

## Prepare once

From the capsule root:

```shell
http --version
jq --version
bat --version
cp .env.example .env
make setup
```

The default journey requires Docker with Compose, Python 3.14, uv, Make, and
ShellCheck. HTTPie, jq, and bat are used for the presenter-facing commands. It
publishes Flask at `http://127.0.0.1:8000`.

## Standalone mini-demo

### 0-15 seconds: show construction

Display [`src/valkey_quickstart/app.py`](../src/valkey_quickstart/app.py) with
syntax highlighting:

```shell
bat --paging=never --style=numbers src/valkey_quickstart/app.py
```

Highlight:

```python
valkey = ValkeyClient()
app = create_app(valkey)
```

Then show the two important commands:

```python
valkey.client.set(DEMO_KEY, stored)
stored = valkey.client.get(DEMO_KEY)
```

Suggested narration:

> The wrapper only creates the connection. The Flask route still shows the
> actual GLIDE commands.

### 15-35 seconds: start the topology

```shell
make start
```

Expected final line:

```text
Flask and Valkey are ready: topology=standalone url=http://127.0.0.1:8000
```

### 35-55 seconds: store and retrieve

```shell
make demo
```

Expected output:

```text
POST /value -> {"value":"hello from standalone"}
GET  /value -> {"value":"hello from standalone"}
```

### 55-60 seconds: close

```shell
make stop
```

Finish with:

> That was one Flask object, one GLIDE client, and normal `SET` and `GET`.

## Manual HTTP version

After `make start`, use HTTPie:

```shell
http --ignore-stdin POST :8000/value value="hello from HTTPie"
http --ignore-stdin GET :8000/value
```

The curl alternative pipes JSON through `jq`:

```shell
curl -sS \
  -H "Content-Type: application/json" \
  -d '{"value":"hello from curl"}' \
  http://127.0.0.1:8000/value |
  jq

curl -sS http://127.0.0.1:8000/value | jq
```

Delete the known demo key:

```shell
make reset
```

This route intentionally performs no schema validation beyond accessing the
`value` field.

## Cluster variation

Start the six-node cluster:

```shell
TOPOLOGY=cluster make start
```

Run the same application journey:

```shell
TOPOLOGY=cluster make demo
```

Expected output changes only in the stored value:

```text
POST /value -> {"value":"hello from cluster"}
GET  /value -> {"value":"hello from cluster"}
```

Stop the selected profile:

```shell
TOPOLOGY=cluster make stop
```

Suggested narration:

> `VALKEY_MODE=cluster` changes construction to `GlideClusterClient`. The
> route and its `SET` and `GET` calls are unchanged.

## Full verification

Run this before publishing the demo:

```shell
make verify
```

It runs formatting, lint, type checks, unit tests, and real HTTP journeys
against the standalone pair and the three-shard cluster.

## Recovery

If port 8000 is occupied:

```shell
FLASK_PORT=8010 make start
FLASK_PORT=8010 make demo
FLASK_PORT=8010 make stop
```

If startup fails, inspect the selected application:

```shell
docker compose --profile standalone logs --tail=100 app-standalone
docker compose --profile cluster logs --tail=100 app-cluster
```

Remove only this capsule's Compose resources:

```shell
docker compose \
  --profile standalone \
  --profile cluster \
  down --remove-orphans --volumes
```

# Topology-Aware Flask Demo Runbook

## Demo goal

Show that the same Flask counter routes work with standalone Valkey, a
Sentinel-managed primary, and Valkey Cluster while `ValkeyStore` keeps all
topology-specific behavior out of the routes.

The shortest presentation is the standalone path. Add the Sentinel and cluster
sections when the session has more time.

## Before recording

From the capsule root, confirm the required tools and install the locked Python
environment:

```shell
docker compose version
python3 --version
uv --version
http --version
jq --version
bat --version
make setup
```

Optional environment overrides belong in `.env`:

```shell
cp .env.example .env
```

The default values require no credentials and publish Flask at
`http://127.0.0.1:8000`.

## Part 1: orient the audience

Display these files before starting the runtime:

```shell
bat --paging=never --style=numbers src/valkey_flask_demo/app.py
bat --paging=never --style=numbers src/valkey_flask_demo/store.py
bat --paging=never --style=numbers compose.yaml
```

Use [`app.py`](../src/valkey_flask_demo/app.py) to show that routes call the
`CounterStore` interface, [`store.py`](../src/valkey_flask_demo/store.py) to
show where topology selection lives, and [`compose.yaml`](../compose.yaml) to
show the three local profiles.

Suggested narration:

> Flask knows how to validate and return counters. `ValkeyStore` knows how to
> connect. Changing the topology does not change route code.

## Part 2: run standalone

Start the default topology:

```shell
make start
```

Expected final line:

```text
Flask and Valkey are ready: topology=standalone url=http://127.0.0.1:8000
```

Run the prepared journey:

```shell
make demo
```

Expected shape:

```text
Topology: standalone
GLIDE client: GlideClient
Counter values: 1 -> 2
Stored value: 2
```

For a manual HTTP explanation, run:

```shell
http --ignore-stdin GET :8000/api/topology
http --ignore-stdin POST :8000/api/counters/video
http --ignore-stdin GET :8000/api/counters/video
http --ignore-stdin DELETE :8000/api/counters/video
```

The equivalent curl commands should format their JSON responses:

```shell
curl -sS http://127.0.0.1:8000/api/topology | jq
curl -sS -X POST http://127.0.0.1:8000/api/counters/video | jq
curl -sS http://127.0.0.1:8000/api/counters/video | jq
curl -sS -X DELETE http://127.0.0.1:8000/api/counters/video | jq
```

Point out that the route always uses `store.increment()`, while the response
reports the selected topology.

Inspect the structured request logs:

```shell
docker compose --profile standalone logs --tail=20 app-standalone
```

Each request-completion log includes a request ID, topology, operation,
duration, status code, and OpenTelemetry correlation fields.

Stop the topology before switching:

```shell
make reset
make stop
```

## Part 3: run Sentinel

Start the Sentinel profile:

```shell
TOPOLOGY=sentinel make start
```

Run the identical journey:

```shell
TOPOLOGY=sentinel make demo
```

Expected shape:

```text
Topology: sentinel
GLIDE client: GlideClient
Sentinel primary: sentinel-primary:6379
Counter values: 1 -> 2
Stored value: 2
```

Show the safe topology response:

```shell
http --ignore-stdin GET :8000/api/topology
```

With curl:

```shell
curl -sS http://127.0.0.1:8000/api/topology | jq
```

Explain that the configured addresses are Sentinel nodes. `ValkeyStore` sends
`SENTINEL GET-MASTER-ADDR-BY-NAME`, closes the temporary discovery client, and
creates the process-lifetime data client for the discovered primary.

Optional log view:

```shell
docker compose --profile sentinel logs --tail=30 app-sentinel
```

Stop the Sentinel profile:

```shell
TOPOLOGY=sentinel make reset
TOPOLOGY=sentinel make stop
```

## Part 4: run Valkey Cluster

Start the cluster profile:

```shell
TOPOLOGY=cluster make start
```

Run the same journey again:

```shell
TOPOLOGY=cluster make demo
```

Expected shape:

```text
Topology: cluster
GLIDE client: GlideClusterClient
Counter values: 1 -> 2
Stored value: 2
```

Suggested narration:

> The HTTP and store operations did not change. Only construction selected
> `GlideClusterClient`, which routes the single counter key to its shard.

Stop the cluster:

```shell
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

## Part 5: show one failure response

Start any topology and submit an invalid counter name:

```shell
make start
http --ignore-stdin --print=Hhb POST \
  'http://127.0.0.1:8000/api/counters/INVALID!'
```

Expected result:

```text
HTTP/1.1 400 BAD REQUEST
```

The response explains the accepted counter-name pattern. This demonstrates
that request validation happens before the key reaches Valkey.

Finish with:

```shell
make stop
```

## Full verification

The complete check runs static analysis, unit tests, and real journeys against
all three topologies:

```shell
make verify
```

Use this before publishing a recording, but do not run it during a short live
demo because it intentionally starts and stops every topology.

## Recovery

If startup fails, inspect the selected application service:

```shell
docker compose --profile standalone logs --tail=100 app-standalone
docker compose --profile sentinel logs --tail=100 app-sentinel
docker compose --profile cluster logs --tail=100 app-cluster
```

Then remove only this capsule's resources:

```shell
docker compose \
  --profile standalone \
  --profile sentinel \
  --profile cluster \
  down --remove-orphans --volumes
```

If port 8000 is busy, choose another loopback port:

```shell
FLASK_PORT=8010 make start
FLASK_PORT=8010 make demo
FLASK_PORT=8010 make stop
```

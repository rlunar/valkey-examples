# Valkey GLIDE Flask Client Quickstart

This is the 60-second version of a Flask and Valkey GLIDE demo. It keeps the
connection choice in one small class and leaves the actual `SET` and `GET`
calls visible in [`app.py`](src/valkey_quickstart/app.py).

Use the longer
[topology-aware Flask capsule](../topology-aware-python-flask/) when a demo
needs validated settings, Sentinel, structured telemetry, readiness endpoints,
or production-oriented error handling.

## What you will see

The same Flask code stores and retrieves one value against either:

- standalone Valkey: one primary and one replica; or
- Valkey Cluster: three primary shards and one replica per shard.

`ValkeyClient` reads `VALKEY_MODE` and `VALKEY_ADDRESSES` directly from the
environment. The capsule assumes those values are correct and fails naturally
when they are missing or unusable.

## 60-second walkthrough

Prerequisites are Docker with Compose, Python 3.14, uv, Make, and ShellCheck.
Install the locked environment once:

```shell
cp .env.example .env
make setup
```

Run the standalone demonstration:

```shell
make start
make demo
make stop
```

Expected output includes the value being stored and then read:

```text
POST /value -> {"value": "hello from standalone"}
GET  /value -> {"value": "hello from standalone"}
```

Run the same application against the six-node cluster:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
make stop
```

## The important code

`app.py` creates the object once:

```python
valkey = ValkeyClient()
app = create_app(valkey)
```

The routes then use the GLIDE client directly:

```python
valkey.client.set(DEMO_KEY, value)
stored = valkey.client.get(DEMO_KEY)
```

There is no store layer, settings model, health endpoint, or custom exception
hierarchy in this quickstart.

## Architecture

The wrapper contains only connection creation. The commands remain in the
Flask module so the complete teaching path fits on one screen.

```mermaid
flowchart LR
    caller["make demo"] -->|"POST/GET /value"| flask["Flask app.py"]
    flask -->|"GLIDE SET / GET"| client["ValkeyClient.client"]
    client -->|"standalone profile"| pair["1 primary + 1 replica"]
    client -->|"cluster profile"| cluster["3 primaries + 3 replicas"]
```

The standalone client receives both node addresses and writes to the primary.
The cluster client starts from the configured seed addresses and routes the
key to its owning shard.

## Configuration

The application reads exactly these variables:

| Variable | Example | Purpose |
| --- | --- | --- |
| `VALKEY_MODE` | `standalone` | Select the standalone or cluster GLIDE client |
| `VALKEY_ADDRESSES` | `standalone-primary:6379,standalone-replica:6379` | Comma-separated bootstrap nodes |
| `FLASK_HOST` | `0.0.0.0` | Waitress bind host |
| `FLASK_PORT` | `8000` | Waitress and loopback publication port |

Compose supplies topology-specific Valkey addresses to the application
container. `.env.example` also contains every variable needed to run the
standalone configuration directly from a compatible network.

## Lifecycle and verification

```shell
make reset
make verify
make stop
```

`make reset` sends `DELETE /value`, which removes only
`valkey-examples:client-quickstart:message`. `make verify` runs Ruff,
ShellCheck, mypy, unit tests, and real integration and HTTP journeys against
both topologies.

## Versions and resource expectations

- Python 3.14.7
- Flask 3.1.3
- valkey-glide-sync 2.5.1
- Valkey 9.1.1

Allow up to 4 CPU cores, 2 GB of memory, 3 GB of disk, 1.5 GB of initial
downloads, and 15 minutes for the full first verification. Normal demo startup
is much shorter once images and packages are cached.

## Security and production limitations

The Flask port binds to loopback. Valkey nodes stay on the private Compose
network, but use no authentication or TLS. Configuration and request bodies
are deliberately trusted, and dependency exceptions are not converted into a
stable error contract. Do not use this capsule as a production deployment
reference.

The default journey requires no credentials and uses no third-party data.
Repository-authored content is MIT licensed; dependencies and container images
retain their own licenses.

This capsule is a candidate owned by `rlunar`, with `valkey-io` as backup.
Repository admission remains blocked until the maintainers, reviewers, and
runtime CI described in the repository root are established.

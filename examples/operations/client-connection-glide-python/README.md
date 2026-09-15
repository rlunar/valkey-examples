# Minimal Valkey GLIDE Python Connection

In this 30-second Python and Valkey GLIDE demo, you run one
[`app.py`](src/valkey_connection/app.py). It loads `.env`, creates either
`GlideClient` or `GlideClusterClient`, runs `SET` and `GET`, prints the value,
and closes the connection.

**Level:** [`L100` — Beginner](../../../docs/authoring.md#choose-the-level)

## Start here

You only need to recognize Python variables, functions, and `if` statements.
The program does four things:

1. reads the Valkey address from `.env`;
2. opens a GLIDE connection;
3. stores and reads one message; and
4. closes the connection.

Key words:

- **client:** the Python object that sends commands to Valkey;
- **standalone:** one Valkey server;
- **cluster:** several Valkey servers that split the keys between them; and
- **bytes:** the form in which GLIDE returns stored text before Python decodes
  it into a string.

Think of GLIDE as a Star Trek communicator: your Python code sends a command
through it and receives Valkey's reply.

Read the code in this order:

1. [`app.py`](src/valkey_connection/app.py) for the complete program;
2. [`.env.example`](.env.example) for the three input values; and
3. [`scripts/start.sh`](scripts/start.sh) only when you want to see how the
   containers start.

## What you will see

When you run the same Python file against either setup, it prints:

```text
hello from GLIDE
```

against either:

- one standalone Valkey node; or
- the minimum three-primary Valkey Cluster.

## Documentation

- [Design and pseudocode](docs/DESIGN.md)
- [30-second video runbook](docs/DEMO.md)
- [Build-from-scratch tutorial](docs/TUTORIAL.md)
- [Short reel script](docs/SCRIPT_REEL.md)
- [Longer tutorial-video script](docs/SCRIPT_VIDEO.md)

## Shared infrastructure

[`example.yaml`](example.yaml) points to the root
[infrastructure capsule](../../../infra/README.md) and selects
`valkey-standalone` or `valkey-cluster-3`. The local `compose.yaml` contains
only the application image.

## Quick start

Prerequisites are Docker with Compose, Python 3.14, uv, Make, ShellCheck, and
bat.

Prepare and start the standalone topology:

```shell
make setup
make start
```

Run the complete application:

```shell
make demo
```

Expected output:

```text
hello from GLIDE
```

Clean up:

```shell
make reset
make stop
```

## Switch to cluster

Change the first two values in `.env`:

```dotenv
VALKEY_MODE=cluster
VALKEY_ADDRESSES=cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
```

Run the same commands:

```shell
make start
make demo
make stop
```

Only the GLIDE constructor changes. The `SET` and `GET` code remains identical.

## The complete application path

```python
load_dotenv()

client = create_client()
try:
    client.set(DEMO_KEY, os.environ["VALKEY_MESSAGE"])
    stored_bytes = client.get(DEMO_KEY)
    print(stored_bytes.decode())
finally:
    client.close()
```

The checked-in implementation keeps the repeated commands in a small `run`
function so unit tests can use the GLIDE boundary without starting Valkey.

## Architecture

The app container and the selected shared-infrastructure topology run in one
capsule-isolated Compose project and private network. No service port is
published to the host.

```mermaid
flowchart LR
    env[".env<br/>mode, addresses, message"] --> app["app.py"]
    app --> infra["Shared infra capsule"]
    infra -->|"GlideClient"| standalone["Standalone<br/>1 node"]
    infra -->|"GlideClusterClient"| cluster["Cluster<br/>3 primary nodes"]
    app -->|"SET then GET"| output["hello from GLIDE"]
```

## Lifecycle and verification

```shell
make setup
make start
make demo
make reset
make verify
make stop
```

`make reset` deletes only
`valkey-examples:client-connection:message`. `make verify` runs Ruff,
ShellCheck, strict mypy, unit tests, and the public application command against
both real topologies.

## Versions and resource expectations

- Python 3.14.7
- valkey-glide-sync 2.5.1
- python-dotenv 1.2.3
- Valkey 9.1.1 Alpine

Allow up to 2 CPU cores, 1 GB of memory, 2 GB of disk, 1 GB of initial
downloads, and 10 minutes for the first full verification. Cached demo runs
are much faster.

## Security and production limitations

Valkey uses no authentication or TLS, but stays on the private Compose network.
Configuration is intentionally trusted and missing values fail naturally. The
three-node cluster has no replicas or failover. This capsule demonstrates
client construction, not a production deployment.

The default journey requires no credentials or third-party data.
Repository-authored content is MIT licensed; dependencies and container images
retain their own licenses.

This capsule is a candidate owned by `rlunar`, with `valkey-io` as backup.
Repository admission remains blocked until the maintainers, reviewers, and
runtime CI described in the repository root are established.

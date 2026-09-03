# Build the Valkey GLIDE Flask Quickstart

## Recording plan

This tutorial creates the quickstart from an empty directory. Each numbered
section is a useful video chapter and ends with a visible checkpoint.

The goal is to keep the connection wrapper small and leave `SET`, `GET`, and
`DEL` visible in `app.py`.

## CLI presentation

Use bat whenever the recording displays source or configuration:

```shell
bat --paging=never --style=numbers pyproject.toml
bat --paging=never --style=numbers src/valkey_quickstart/valkey_client.py
bat --paging=never --style=numbers src/valkey_quickstart/app.py
```

Use HTTPie for interactive route calls. Keep curl as an alternative and pipe
its JSON responses through `jq`.

## 1. Initialize the application

```shell
mkdir client-quickstart-python-flask
cd client-quickstart-python-flask
uv init \
  --app \
  --package \
  --python 3.14 \
  --name valkey-client-quickstart-flask \
  --vcs none \
  --build-backend setuptools
```

Create the source and test folders:

```shell
mkdir -p \
  docs \
  scripts \
  src/valkey_quickstart \
  tests/integration \
  tests/journey \
  tests/unit
touch src/valkey_quickstart/__init__.py
touch src/valkey_quickstart/py.typed
```

Checkpoint:

```shell
bat --paging=never --style=numbers pyproject.toml .python-version
find src -maxdepth 2 -type f
```

## 2. Add dependencies

Use the distribution names published by the packages:

```shell
uv add \
  Flask==3.1.3 \
  python-dotenv==1.2.3 \
  valkey-glide-sync==2.5.1 \
  waitress==3.0.2
```

Add development tools:

```shell
uv add --dev \
  mypy==2.3.1 \
  pytest==9.1.1 \
  pytest-cov==7.1.0 \
  ruff==0.16.4
```

`python-dotenv` is imported as `dotenv`. `valkey-glide-sync` is imported as
`glide_sync`.

Checkpoint:

```shell
uv run python -c "import flask, dotenv, glide_sync"
```

## 3. Create `ValkeyClient`

Create `src/valkey_quickstart/valkey_client.py`:

```python
from __future__ import annotations

import os

from dotenv import load_dotenv
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
)

load_dotenv()

type GlideClientType = GlideClient | GlideClusterClient


class ValkeyClient:
    def __init__(self) -> None:
        addresses = []
        for address in os.environ["VALKEY_ADDRESSES"].split(","):
            host, port = address.strip().rsplit(":", maxsplit=1)
            addresses.append(NodeAddress(host=host, port=int(port)))

        if os.environ["VALKEY_MODE"] == "cluster":
            self.client: GlideClientType = GlideClusterClient.create(
                GlideClusterClientConfiguration(addresses=addresses)
            )
        else:
            self.client = GlideClient.create(
                GlideClientConfiguration(addresses=addresses)
            )

    def close(self) -> None:
        self.client.close()
```

Explain the deliberate omissions:

- no default for required variables;
- no Pydantic settings model;
- no custom configuration error;
- no Sentinel branch; and
- no command wrapper.

Checkpoint: point to the public `client` attribute. The next file will use it
directly.

## 4. Create the Flask application

Create `src/valkey_quickstart/app.py`:

```python
from __future__ import annotations

import atexit
import os
from typing import Any

from flask import Flask, jsonify, request
from waitress import serve  # type: ignore[import-untyped]

from valkey_quickstart.valkey_client import ValkeyClient

DEMO_KEY = "valkey-examples:client-quickstart:message"


def create_app(valkey: ValkeyClient | None = None) -> Flask:
    valkey = valkey or ValkeyClient()
    app = Flask(__name__)
    app.extensions["valkey_client"] = valkey

    @app.route("/value", methods=["GET", "POST", "DELETE"])
    def value() -> tuple[Any, int]:
        if request.method == "POST":
            stored = request.get_json()["value"]
            valkey.client.set(DEMO_KEY, stored)
            return jsonify({"value": stored}), 200

        if request.method == "DELETE":
            valkey.client.delete([DEMO_KEY])
            return jsonify({"deleted": True}), 200

        stored = valkey.client.get(DEMO_KEY)
        value = stored.decode() if stored is not None else None
        return jsonify({"value": value}), 200

    return app


def main() -> None:
    valkey = ValkeyClient()
    atexit.register(valkey.close)
    app = create_app(valkey)
    serve(
        app,
        host=os.environ["FLASK_HOST"],
        port=int(os.environ["FLASK_PORT"]),
        threads=4,
    )
```

Add this project script to `pyproject.toml`:

```toml
[project.scripts]
valkey-quickstart = "valkey_quickstart.app:main"
```

Checkpoint: highlight that the data path is visible in three lines:

```python
valkey.client.set(DEMO_KEY, stored)
stored = valkey.client.get(DEMO_KEY)
valkey.client.delete([DEMO_KEY])
```

Do not add health endpoints; the quickstart has one teaching route.

## 5. Add `.env`

Create `.env.example`:

```dotenv
VALKEY_MODE=standalone
VALKEY_ADDRESSES=standalone-primary:6379,standalone-replica:6379

FLASK_HOST=0.0.0.0
FLASK_PORT=8000
```

Copy it for local use:

```shell
cp .env.example .env
```

The host names resolve inside the Compose network. Compose also supplies the
correct values directly to each application service.

Checkpoint: remove `VALKEY_ADDRESSES` temporarily and show that startup fails
with `KeyError`. Restore the value before continuing. This is the intended
fail-fast behavior.

## 6. Configure quality tools

Add the package and test settings to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-ra --strict-config --strict-markers"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.mypy]
python_version = "3.14"
strict = true
packages = ["valkey_quickstart"]
```

Tell setuptools to include `py.typed` so the package advertises type
information.

Checkpoint:

```shell
uv run ruff check src
uv run mypy
```

## 7. Add focused unit tests

In `tests/unit/test_valkey_client.py`, patch the GLIDE `create()` methods and
verify:

- standalone mode creates `GlideClient`;
- cluster mode creates `GlideClusterClient`;
- comma-separated addresses become `NodeAddress` objects; and
- `close()` closes the selected client.

In `tests/unit/test_app.py`, inject a fake `ValkeyClient` whose public `client`
implements `set`, `get`, and `delete`. Test the three `/value` methods.

Checkpoint:

```shell
uv run pytest tests/unit
```

## 8. Add the container image

Create a `Dockerfile` that:

1. uses the pinned Python 3.14 slim image;
2. installs the pinned uv version;
3. copies `pyproject.toml`, `uv.lock`, and `.python-version`;
4. runs `uv sync --frozen`;
5. copies `src/` and `tests/`;
6. switches to a non-root user; and
7. runs `valkey-quickstart`.

Keep the Valkey ports private. Only Flask needs a loopback host publication.

## 9. Add standalone Compose services

Begin `compose.yaml` with:

- one `standalone-primary`;
- one `standalone-replica` using `--replicaof`;
- one `app-standalone`; and
- a private `demo` network.

Set the application environment:

```yaml
environment:
  FLASK_HOST: 0.0.0.0
  FLASK_PORT: ${FLASK_PORT:-8000}
  VALKEY_ADDRESSES: standalone-primary:6379,standalone-replica:6379
  VALKEY_MODE: standalone
```

Checkpoint:

```shell
docker compose --profile standalone config --quiet
```

## 10. Add the three-shard cluster

Add six cluster-enabled Valkey services. Add a one-shot `cluster-init` service
that runs:

```text
valkey-cli --cluster create <six nodes> --cluster-replicas 1 --cluster-yes
```

Add `app-cluster` with:

```yaml
environment:
  FLASK_HOST: 0.0.0.0
  FLASK_PORT: ${FLASK_PORT:-8000}
  VALKEY_ADDRESSES: cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
  VALKEY_MODE: cluster
```

Use the complete final
[`compose.yaml`](../compose.yaml) for the node health checks and pinned image
digest.

Checkpoint:

```shell
docker compose --profile cluster config --quiet
```

## 11. Add the demo lifecycle

Create:

- `scripts/start.sh` to select the profile, build, and wait for `GET /value`;
- `scripts/demo.py` to POST and GET `hello from <topology>`;
- `scripts/reset.py` to send `DELETE /value`;
- `scripts/stop.sh` to remove only this Compose project; and
- `scripts/test-real.sh` to exercise standalone and cluster.

Create a `Makefile` exposing:

```text
make setup
make start
make demo
make reset
make verify
make stop
```

The Make targets should call the visible uv, Python, shell, and Compose
commands rather than hiding the workflow in another framework.

## 12. Add real tests

Create `tests/integration/test_client.py` to execute `SET`, `GET`, and `DEL`
through a real `ValkeyClient`.

Create `tests/journey/test_http.py` to:

1. POST a value;
2. GET the same value;
3. DELETE it; and
4. confirm the next GET returns `null`.

Run both contracts against the standalone and cluster profiles from
`scripts/test-real.sh`.

## 13. Run the completed demo

Standalone:

```shell
make setup
make start
make demo
make reset
make stop
```

Cluster:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
TOPOLOGY=cluster make stop
```

Complete verification:

```shell
make verify
```

End the recording in `app.py`: the viewer should be able to see object
construction, `SET`, and `GET` without navigating through another layer.

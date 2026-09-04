# Build the Minimal Valkey GLIDE Python Connection

This tutorial creates the complete capsule. For a 30-second reel, record only
the `.env`, `app.py`, and `make demo` sections. The remaining sections explain
the repeatable Docker environment used behind the recording.

## 1. Initialize Python

Create the project:

```shell
uv init --package client-connection-glide-python
cd client-connection-glide-python
```

Add the two runtime dependencies:

```shell
uv add python-dotenv valkey-glide-sync
```

Add development tools:

```shell
uv add --dev pytest pytest-cov ruff mypy
```

The finished capsule pins Python in `.python-version`:

```text
3.14.7
```

Its final runtime dependency list in `pyproject.toml` is:

```toml
[project]
name = "valkey-client-connection-glide-python"
version = "0.1.0"
description = "A minimal standalone and cluster Valkey GLIDE connection demo"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
  "python-dotenv==1.2.3",
  "valkey-glide-sync==2.5.1",
]

[project.scripts]
valkey-connect = "valkey_connection.app:main"
```

## 2. Add `.env`

Create `.env.example`:

```dotenv
# Use these values for standalone:
VALKEY_MODE=standalone
VALKEY_ADDRESSES=standalone:6379

# To use the cluster, replace the two lines above with:
# VALKEY_MODE=cluster
# VALKEY_ADDRESSES=cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379

VALKEY_MESSAGE=hello from GLIDE
```

Copy it:

```shell
cp .env.example .env
```

There is intentionally no settings class. Missing or malformed values fail
through normal Python or GLIDE exceptions.

## 3. Create the complete application

Create `src/valkey_connection/app.py`:

```python
"""Connect to Valkey, store one value, and read it back."""

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

type ValkeyClient = GlideClient | GlideClusterClient

DEMO_KEY = "valkey-examples:client-connection:message"


def create_client() -> ValkeyClient:
    """Create the selected GLIDE client from the trusted environment."""

    addresses = []
    for address in os.environ["VALKEY_ADDRESSES"].split(","):
        host, port = address.split(":")
        addresses.append(NodeAddress(host=host, port=int(port)))

    if os.environ["VALKEY_MODE"] == "cluster":
        return GlideClusterClient.create(
            GlideClusterClientConfiguration(addresses=addresses)
        )

    return GlideClient.create(
        GlideClientConfiguration(addresses=addresses)
    )


def run(client: ValkeyClient) -> str:
    """Store the configured message and print the value read from Valkey."""

    client.set(DEMO_KEY, os.environ["VALKEY_MESSAGE"])
    stored = client.get(DEMO_KEY)
    assert stored is not None
    value = stored.decode()
    print(value)
    return value


def main() -> None:
    """Create the selected client, run the demo, and close the connection."""

    client = create_client()
    try:
        run(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()
```

The complete explanation is five actions:

1. `load_dotenv()` loads the configuration.
2. Addresses become GLIDE `NodeAddress` objects.
3. `VALKEY_MODE` selects the standalone or cluster constructor.
4. `SET` stores the message and `GET` reads it.
5. `finally` closes the native client.

Display the entire teaching path:

```shell
bat --paging=never --style=numbers src/valkey_connection/app.py
```

## 4. The 30-second reel path

Once the Docker environment is prepared, the complete on-camera interaction
is:

```shell
bat --paging=never --style=numbers src/valkey_connection/app.py
make demo
```

Expected output:

```text
hello from GLIDE
```

Everything below this point creates the repeatable environment behind those
two commands.

## 5. Create the application image

GLIDE contains native code, so the Python app uses a glibc-based image. Valkey
uses its official Alpine image.

Create `Dockerfile`:

```dockerfile
FROM python:3.14.7-slim-trixie@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir uv==0.12.9 \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

WORKDIR /app

COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --frozen --no-install-project

COPY src ./src
COPY tests ./tests
RUN uv sync --frozen \
    && rm -rf /tmp/uv-cache \
    && chown -R app:app /app

USER app

ENTRYPOINT ["uv", "run", "--frozen", "--no-sync"]
CMD ["valkey-connect"]
```

The dependency files are copied before source so Docker can cache dependency
installation. The final process runs as the unprivileged `app` user.

## 6. Create both Valkey topologies

Create `compose.yaml`:

```yaml
name: valkey-example-client-connection-glide-python

x-valkey: &valkey
  image: valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9
  restart: "no"
  networks:
    - demo
  security_opt:
    - no-new-privileges:true
  healthcheck:
    test: ["CMD", "valkey-cli", "-h", "127.0.0.1", "-p", "6379", "ping"]
    interval: 1s
    timeout: 1s
    retries: 30
    start_period: 2s

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: valkey-example-client-connection-glide-python:local
    restart: "no"
    init: true
    env_file:
      - path: .env
        required: false
    volumes:
      - ./.env:/app/.env:ro
    networks:
      - demo
    security_opt:
      - no-new-privileges:true

  standalone:
    <<: *valkey
    profiles: ["standalone"]
    command:
      - valkey-server
      - --appendonly
      - "no"
      - --save
      - ""
      - --protected-mode
      - "no"
    tmpfs:
      - /data

  cluster-node-1:
    <<: *valkey
    profiles: ["cluster"]
    command:
      - valkey-server
      - --appendonly
      - "no"
      - --save
      - ""
      - --protected-mode
      - "no"
      - --cluster-enabled
      - "yes"
      - --cluster-config-file
      - /data/nodes.conf
      - --cluster-node-timeout
      - "5000"
      - --cluster-announce-hostname
      - cluster-node-1
      - --cluster-announce-port
      - "6379"
      - --cluster-announce-bus-port
      - "16379"
      - --cluster-preferred-endpoint-type
      - hostname
    tmpfs:
      - /data

  cluster-node-2:
    <<: *valkey
    profiles: ["cluster"]
    command:
      - valkey-server
      - --appendonly
      - "no"
      - --save
      - ""
      - --protected-mode
      - "no"
      - --cluster-enabled
      - "yes"
      - --cluster-config-file
      - /data/nodes.conf
      - --cluster-node-timeout
      - "5000"
      - --cluster-announce-hostname
      - cluster-node-2
      - --cluster-announce-port
      - "6379"
      - --cluster-announce-bus-port
      - "16379"
      - --cluster-preferred-endpoint-type
      - hostname
    tmpfs:
      - /data

  cluster-node-3:
    <<: *valkey
    profiles: ["cluster"]
    command:
      - valkey-server
      - --appendonly
      - "no"
      - --save
      - ""
      - --protected-mode
      - "no"
      - --cluster-enabled
      - "yes"
      - --cluster-config-file
      - /data/nodes.conf
      - --cluster-node-timeout
      - "5000"
      - --cluster-announce-hostname
      - cluster-node-3
      - --cluster-announce-port
      - "6379"
      - --cluster-announce-bus-port
      - "16379"
      - --cluster-preferred-endpoint-type
      - hostname
    tmpfs:
      - /data

  cluster-init:
    image: valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9
    profiles: ["cluster"]
    restart: "no"
    command:
      - valkey-cli
      - --cluster
      - create
      - cluster-node-1:6379
      - cluster-node-2:6379
      - cluster-node-3:6379
      - --cluster-yes
    networks:
      - demo
    security_opt:
      - no-new-privileges:true

networks:
  demo:
    driver: bridge
```

Only the app container needs `.env`. No port is published because the app runs
inside the same private network.

Inspect and validate the stack:

```shell
yq '.services | keys' compose.yaml
docker compose --profile standalone config --quiet
docker compose --profile cluster config --quiet
```

## 7. Add the lifecycle scripts

Create `scripts/common.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

read_dotenv_value() {
  local name="$1"

  [[ -f .env ]] || return 1
  awk -F= -v key="$name" \
    '$1 == key { sub(/^[^=]*=/, ""); print; exit }' .env
}

dotenv_mode="$(read_dotenv_value VALKEY_MODE || true)"
dotenv_addresses="$(read_dotenv_value VALKEY_ADDRESSES || true)"
dotenv_message="$(read_dotenv_value VALKEY_MESSAGE || true)"

export TOPOLOGY="${TOPOLOGY:-${dotenv_mode:-standalone}}"
export VALKEY_ADDRESSES="${
  VALKEY_ADDRESSES:-${dotenv_addresses:-standalone:6379}
}"
export VALKEY_MESSAGE="${
  VALKEY_MESSAGE:-${dotenv_message:-hello from GLIDE}
}"

case "$TOPOLOGY" in
  standalone | cluster)
    ;;
  *)
    printf \
      'VALKEY_MODE must be standalone or cluster; received %s\n' \
      "$TOPOLOGY" >&2
    exit 2
    ;;
esac

compose() {
  docker compose --profile "$TOPOLOGY" "$@"
}

compose_all() {
  docker compose --profile standalone --profile cluster "$@"
}
```

Create `scripts/start.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if [[ "$TOPOLOGY" == "standalone" ]]; then
  compose up -d --wait standalone
else
  compose up -d --wait cluster-node-1 cluster-node-2 cluster-node-3

  if ! compose exec -T cluster-node-1 \
    valkey-cli cluster info | grep -q '^cluster_state:ok'; then
    compose run --rm --no-deps cluster-init
  fi

  for _ in {1..40}; do
    if compose exec -T cluster-node-1 \
      valkey-cli cluster info | grep -q '^cluster_state:ok'; then
      break
    fi
    sleep 0.25
  done

  compose exec -T cluster-node-1 \
    valkey-cli cluster info | grep -q '^cluster_state:ok'
fi

printf 'Valkey is ready: topology=%s\n' "$TOPOLOGY"
```

Create `scripts/demo.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose run \
  --rm \
  --no-deps \
  -e VALKEY_MODE="$TOPOLOGY" \
  -e VALKEY_ADDRESSES="$VALKEY_ADDRESSES" \
  -e VALKEY_MESSAGE="$VALKEY_MESSAGE" \
  app
```

Create `scripts/reset.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

demo_key="valkey-examples:client-connection:message"

if [[ "$TOPOLOGY" == "cluster" ]]; then
  compose exec -T cluster-node-1 \
    valkey-cli -c del "$demo_key" >/dev/null
else
  compose exec -T standalone \
    valkey-cli del "$demo_key" >/dev/null
fi

printf 'Deleted the demo key.\n'
```

Create `scripts/stop.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_all down --remove-orphans --volumes
printf 'Stopped resources owned by client-connection-glide-python.\n'
```

Create `scripts/test-real.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

cleanup() {
  docker compose \
    --profile standalone \
    --profile cluster \
    down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for topology in standalone cluster; do
  if [[ "$topology" == "cluster" ]]; then
    addresses="cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379"
  else
    addresses="standalone:6379"
  fi
  message="hello from ${topology}"

  printf '\n== Verify %s ==\n' "$topology"
  cleanup

  TOPOLOGY="$topology" ./scripts/start.sh

  output="$(
    TOPOLOGY="$topology" \
      VALKEY_ADDRESSES="$addresses" \
      VALKEY_MESSAGE="$message" \
      ./scripts/demo.sh
  )"
  printf '%s\n' "$output"
  grep -Fx "$message" <<<"$output" >/dev/null

  TOPOLOGY="$topology" \
    VALKEY_ADDRESSES="$addresses" \
    VALKEY_MESSAGE="$message" \
    docker compose --profile "$topology" run \
      --rm \
      --no-deps \
      -e VALKEY_MODE="$topology" \
      -e VALKEY_ADDRESSES="$addresses" \
      -e VALKEY_MESSAGE="$message" \
      app \
      pytest tests/integration

  TOPOLOGY="$topology" ./scripts/reset.sh
  TOPOLOGY="$topology" ./scripts/stop.sh
done
```

Mark the scripts executable:

```shell
chmod +x scripts/*.sh
```

The shell files do not duplicate application behavior. They only select a
profile, wait for Valkey, run the one-shot app, and clean up its known state.

## 8. Add tests

The unit tests use a fake only at the Valkey boundary. They verify the public
`run()` behavior and both constructor choices.

Create `tests/unit/test_app.py`:

```python
"""Behavior tests for the minimal application."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from valkey_connection.app import create_client, run


class FakeClient:
    """The Valkey boundary needed by the public run function."""

    def __init__(self) -> None:
        self.values: dict[str, bytes] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value.encode()

    def get(self, key: str) -> bytes | None:
        return self.values.get(key)


def test_run_stores_retrieves_and_prints_the_configured_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("VALKEY_MESSAGE", "hello from the test")

    result = run(FakeClient())

    assert result == "hello from the test"
    assert capsys.readouterr().out == "hello from the test\n"


@patch("valkey_connection.app.GlideClient.create")
def test_create_client_connects_to_the_standalone_addresses(
    create: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VALKEY_MODE", "standalone")
    monkeypatch.setenv("VALKEY_ADDRESSES", "valkey:6379")

    client = create_client()

    config = create.call_args.args[0]
    assert [
        (address.host, address.port)
        for address in config.addresses
    ] == [("valkey", 6379)]
    assert client is create.return_value


@patch("valkey_connection.app.GlideClusterClient.create")
def test_create_client_connects_to_the_cluster_seed_addresses(
    create: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VALKEY_MODE", "cluster")
    monkeypatch.setenv(
        "VALKEY_ADDRESSES",
        "node-1:6379,node-2:6379,node-3:6379",
    )

    client = create_client()

    config = create.call_args.args[0]
    assert [
        (address.host, address.port)
        for address in config.addresses
    ] == [
        ("node-1", 6379),
        ("node-2", 6379),
        ("node-3", 6379),
    ]
    assert client is create.return_value
```

Create `tests/integration/test_app.py`:

```python
"""Run the public application command against real Valkey."""

from __future__ import annotations

import os

import pytest

from valkey_connection.app import main


@pytest.mark.integration
def test_app_prints_the_value_read_from_valkey(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main()

    assert capsys.readouterr().out == (
        f"{os.environ['VALKEY_MESSAGE']}\n"
    )
```

The real test script starts each topology, executes `app.py`, runs the
integration test in the same app image, resets the key, and cleans up.

## 9. Add the Make interface

Create the complete `Makefile`:

<!-- markdownlint-disable MD010 -->

```makefile
SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start demo reset stop format lint typecheck test-unit \
	test-real verify-static verify

help:
	@printf '%s\n' \
		"setup        Install dependencies and build the app image" \
		"start        Start the topology selected in .env" \
		"demo         Run app.py once and print the stored value" \
		"reset        Delete the one known demo key" \
		"stop         Stop this capsule's Compose resources" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run app.py against standalone and cluster" \
		"verify       Run every static and behavioral check"

setup:
	test -f .env || cp .env.example .env
	uv sync --frozen
	docker compose build app

start:
	./scripts/start.sh

demo:
	./scripts/demo.sh

reset:
	./scripts/reset.sh

stop:
	./scripts/stop.sh

format:
	uv run --frozen ruff format src tests
	uv run --frozen ruff check --fix src tests

lint:
	uv run --frozen ruff format --check src tests
	uv run --frozen ruff check src tests
	shellcheck -x scripts/*.sh

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest tests/unit --cov --cov-report=term-missing

test-real:
	./scripts/test-real.sh

verify-static: lint typecheck
	docker compose --profile standalone --profile cluster config --quiet
	../../../tools/ci/check-structure.sh

verify: setup verify-static test-unit test-real
```

<!-- markdownlint-enable MD010 -->

The Makefile delegates to the same commands shown in the tutorial rather than
hiding application behavior in Make logic.

## 10. Run standalone

Keep the default `.env`, then run:

```shell
make setup
make start
make demo
```

Expected output:

```text
hello from GLIDE
```

Clean the key and containers:

```shell
make reset
make stop
```

## 11. Run cluster

Change `.env`:

```dotenv
VALKEY_MODE=cluster
VALKEY_ADDRESSES=cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
VALKEY_MESSAGE=hello from GLIDE
```

Run the same application:

```shell
make start
make demo
make reset
make stop
```

The output is unchanged because only client construction differs.

## 12. Verify everything

```shell
make verify
```

This runs formatting checks, Ruff, ShellCheck, strict mypy, unit tests, and the
same one-shot application against real standalone and cluster deployments.

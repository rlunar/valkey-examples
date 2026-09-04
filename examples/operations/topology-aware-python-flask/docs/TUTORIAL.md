# Build the Topology-Aware Flask Demo

## Recording plan

This tutorial builds the capsule in recordable stages. Each stage ends with a
small checkpoint so a video can pause, explain the result, and continue.

The final implementation is in the parent capsule. Keep it open as the
reference while recording.

## CLI presentation

Display source and configuration files through bat so syntax highlighting and
line numbers remain visible in the recording:

```shell
bat --paging=never --style=numbers pyproject.toml
bat --paging=never --style=numbers src/valkey_flask_demo/app.py
bat --paging=never --style=numbers compose.yaml
```

Use HTTPie for interactive route calls. When showing an equivalent curl
command, pipe JSON responses through `jq`.

## 1. Initialize the project

Create an empty directory and initialize a packaged Python application:

```shell
mkdir topology-aware-python-flask
cd topology-aware-python-flask
uv init \
  --app \
  --package \
  --python 3.14 \
  --name valkey-topology-aware-flask-demo \
  --vcs none \
  --build-backend setuptools
```

Create the application and test layout:

```shell
mkdir -p \
  docs \
  infra/sentinel \
  scripts \
  src/valkey_flask_demo \
  tests/integration \
  tests/journey \
  tests/unit
touch src/valkey_flask_demo/__init__.py
touch src/valkey_flask_demo/py.typed
```

Checkpoint:

```shell
bat --paging=never --style=numbers pyproject.toml .python-version
find src -maxdepth 2 -type f
```

## 2. Add runtime and development dependencies

Add the pinned runtime packages:

```shell
uv add \
  Flask==3.1.3 \
  opentelemetry-api==1.44.0 \
  opentelemetry-exporter-otlp-proto-http==1.44.0 \
  opentelemetry-instrumentation-flask==0.65b0 \
  opentelemetry-instrumentation-logging==0.65b0 \
  opentelemetry-sdk==1.44.0 \
  pydantic==2.13.4 \
  pydantic-settings==2.15.0 \
  valkey-glide-sync==2.5.1 \
  waitress==3.0.2
```

Add the test and quality tools:

```shell
uv add --dev \
  httpx==0.28.1 \
  mypy==2.3.1 \
  pytest==9.1.1 \
  pytest-cov==7.1.0 \
  ruff==0.16.4
```

The import name for `valkey-glide-sync` is `glide_sync`. Pydantic Settings
loads `.env` directly, so this version does not need a separate dotenv
dependency.

Checkpoint:

```shell
uv lock --check
uv run python -c "import flask, glide_sync, pydantic"
```

Finish `pyproject.toml` before writing source:

```toml
[build-system]
requires = ["setuptools==80.9.0"]
build-backend = "setuptools.build_meta"

[project]
name = "valkey-topology-aware-flask-demo"
version = "0.1.0"
description = "A maintainable Flask foundation for standalone, Sentinel, and cluster Valkey topologies"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
  "Flask==3.1.3",
  "opentelemetry-api==1.44.0",
  "opentelemetry-exporter-otlp-proto-http==1.44.0",
  "opentelemetry-instrumentation-flask==0.65b0",
  "opentelemetry-instrumentation-logging==0.65b0",
  "opentelemetry-sdk==1.44.0",
  "pydantic==2.13.4",
  "pydantic-settings==2.15.0",
  "valkey-glide-sync==2.5.1",
  "waitress==3.0.2",
]

[project.scripts]
valkey-flask-demo = "valkey_flask_demo.app:main"

[dependency-groups]
dev = [
  "httpx==0.28.1",
  "mypy==2.3.1",
  "pytest==9.1.1",
  "pytest-cov==7.1.0",
  "ruff==0.16.4",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
valkey_flask_demo = ["py.typed"]

[tool.pytest.ini_options]
addopts = "-ra --strict-config --strict-markers"
testpaths = ["tests"]
markers = [
  "integration: requires a real Valkey topology",
  "journey: exercises the running Flask application",
]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.mypy]
python_version = "3.14"
strict = true
packages = ["valkey_flask_demo"]

[tool.coverage.run]
branch = true
source = ["valkey_flask_demo"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

Regenerate the lockfile:

```shell
uv lock
uv sync --frozen
```

## 3. Create validated settings

Create `src/valkey_flask_demo/config.py`.

Start with the topology enum:

```python
from enum import StrEnum


class Topology(StrEnum):
    STANDALONE = "standalone"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"
```

Then create an immutable `AppSettings` model backed by environment variables:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    topology: Topology = Field(
        default=Topology.STANDALONE,
        validation_alias="VALKEY_TOPOLOGY",
    )
    valkey_addresses: str = Field(
        default="127.0.0.1:6379",
        validation_alias="VALKEY_ADDRESSES",
    )
    sentinel_master: str = Field(
        default="demo-primary",
        validation_alias="VALKEY_SENTINEL_MASTER",
    )
    flask_host: str = Field(default="127.0.0.1", validation_alias="FLASK_HOST")
    flask_port: int = Field(default=8000, validation_alias="FLASK_PORT")
```

Add the remaining database, timeout, key-prefix, thread, logging, and
OpenTelemetry fields from the final
[`config.py`](../src/valkey_flask_demo/config.py). Implement `addresses()` once
so every client path receives validated `(host, port)` tuples.

Add a model validator for two cross-field rules:

```text
parse every configured address
if topology is cluster, require database zero
if an OTLP endpoint exists, require http:// or https://
```

Checkpoint:

```shell
VALKEY_TOPOLOGY=cluster \
VALKEY_ADDRESSES=node-1:6379,node-2:6379 \
uv run python -c \
  "from valkey_flask_demo.config import AppSettings; print(AppSettings().addresses())"
```

## 4. Define response models

Create `src/valkey_flask_demo/models.py` with two frozen Pydantic models:

```python
class CounterSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    value: int = Field(ge=0)
    topology: Topology


class TopologySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    topology: Topology
    configured_addresses: tuple[str, ...]
    client: str
    sentinel_master: str | None = None
    discovered_primary: str | None = None
```

Checkpoint: explain that these models define the HTTP contract, while
`AppSettings` defines the environment contract.

## 5. Design the store interface

Create `src/valkey_flask_demo/store.py`. Begin with the narrow interface Flask
needs:

```python
class CounterStore(Protocol):
    def get(self, name: str) -> int: ...
    def increment(self, name: str) -> int: ...
    def delete(self, name: str) -> bool: ...
    def ping(self) -> None: ...
    def topology_snapshot(self) -> TopologySnapshot: ...
    def close(self) -> None: ...
```

Add `ValkeyUnavailable` as the dependency-facing exception. Then create
`ValkeyStore` with one settings object and one process-lifetime client.

Implement the public commands first:

```python
def get(self, name: str) -> int:
    value = self._run(lambda client: client.get(self._counter_key(name)))
    return 0 if value is None else int(value)


def increment(self, name: str) -> int:
    return self._run(lambda client: client.incr(self._counter_key(name)))


def delete(self, name: str) -> bool:
    return self._run(
        lambda client: client.delete([self._counter_key(name)])
    ) > 0
```

Keep key construction private:

```python
def _counter_key(self, name: str) -> str:
    return f"{self._settings.key_prefix}:counter:{name}"
```

Checkpoint: at this point the Flask-facing API is complete even though
topology construction is not.

## 6. Add standalone and cluster clients

In `_connect()`, select the GLIDE client:

```text
cluster:
    GlideClusterClient.create(GlideClusterClientConfiguration(...))

standalone:
    GlideClient.create(GlideClientConfiguration(...))
```

Pass the settings-derived addresses, request timeout, connection timeout, and
client name. Use `NodeDiscoveryMode.STANDARD` for normal standalone
connections.

Wrap non-Sentinel commands in `_run()` and translate `GlideError` into
`ValkeyUnavailable`. This keeps GLIDE exceptions out of Flask.

Checkpoint: write unit tests that patch the two `create()` methods and assert
that the selected client matches the topology.

## 7. Add Sentinel discovery

Add a private `_discover_sentinel_primary()` method:

```text
for each Sentinel address:
    create a temporary GlideClient
    use RESP2 and NodeDiscoveryMode.STATIC
    send SENTINEL GET-MASTER-ADDR-BY-NAME <group>
    validate [host, port]
    close the temporary client
    return the primary
raise ValkeyUnavailable if every Sentinel fails
```

Use the discovered address to create a static standalone data client.

Add an `RLock` around Sentinel-backed commands. When a command raises
`GlideError`, rediscover the primary, replace the client, close the old client,
and retry once.

Checkpoint: test malformed Sentinel responses and verify that a failed command
causes exactly one client replacement and one retry.

## 8. Configure logging and tracing

Create `src/valkey_flask_demo/telemetry.py`.

First add `JsonLogFormatter`, which emits:

```text
timestamp
severity
logger
message
service_name
trace_id
span_id
request_id
topology
operation
duration_ms
status_code
```

Then add `configure_observability(settings)`:

```text
configure the root logger once
always add the JSON console handler
if OTEL_ENABLED:
    instrument logging
    create a resource and tracer provider
    if an OTLP endpoint exists:
        export spans to /v1/traces
        export logs to /v1/logs
        initialize GLIDE trace export
```

Finally add `instrument_flask(app, settings)` to attach Flask request
instrumentation only when enabled.

Checkpoint:

```shell
uv run python -c \
  "from valkey_flask_demo.config import AppSettings; from valkey_flask_demo.telemetry import configure_observability; configure_observability(AppSettings())"
```

## 9. Build the Flask adapter

Create `src/valkey_flask_demo/app.py`.

Define a `TypeAdapter` for counter names, then create `FlaskDemo`:

```python
class FlaskDemo:
    def __init__(self, settings: AppSettings, store: CounterStore) -> None:
        self.settings = settings
        self.store = store
        self.app = Flask(__name__)
        instrument_flask(self.app, settings)
        self._register_hooks()
        self._register_routes()
        self._register_error_handlers()
```

Register these routes:

| Route | Store call |
| --- | --- |
| `GET /health/ready` | `ping()` |
| `GET /api/topology` | `topology_snapshot()` |
| `GET /api/counters/<name>` | `get()` |
| `POST /api/counters/<name>` | `increment()` |
| `DELETE /api/counters/<name>` | `delete()` |

Add request hooks that create a UUIDv7 request ID, measure duration, attach
`X-Request-ID`, and log the completed request.

Translate Pydantic validation failures to HTTP 400 and `ValkeyUnavailable` to
HTTP 503.

Finish with the application factory:

```python
def create_app(
    settings: AppSettings | None = None,
    store: CounterStore | None = None,
) -> Flask:
    runtime_settings = settings or AppSettings()
    configure_observability(runtime_settings)
    runtime_store = store or ValkeyStore(runtime_settings)
    return FlaskDemo(runtime_settings, runtime_store).app
```

In `main()`, register the store's `close()` method with `atexit` and run the
app with Waitress.

Checkpoint: inject a fake store into `create_app()` and exercise every route
with Flask's test client.

## 10. Assemble the complete application files

The earlier sections explained the modules in conceptual order. Before adding
containers, replace each module with its complete runnable version.

### 10.1 Complete `config.py`

Create `src/valkey_flask_demo/config.py`:

```python
"""Validated environment-backed configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

type Address = tuple[str, int]


class Topology(StrEnum):
    """Valkey deployment shape selected by the application."""

    STANDALONE = "standalone"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


class AppSettings(BaseSettings):
    """Immutable application and Valkey settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    topology: Topology = Field(
        default=Topology.STANDALONE,
        validation_alias="VALKEY_TOPOLOGY",
    )
    valkey_addresses: str = Field(
        default="127.0.0.1:6379",
        min_length=3,
        max_length=2048,
        validation_alias="VALKEY_ADDRESSES",
    )
    sentinel_master: str = Field(
        default="demo-primary",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$",
        validation_alias="VALKEY_SENTINEL_MASTER",
    )
    database_id: int = Field(
        default=0,
        ge=0,
        le=15,
        validation_alias="VALKEY_DATABASE_ID",
    )
    request_timeout_ms: int = Field(
        default=1_000,
        ge=50,
        le=30_000,
        validation_alias="VALKEY_REQUEST_TIMEOUT_MS",
    )
    connection_timeout_ms: int = Field(
        default=2_000,
        ge=100,
        le=30_000,
        validation_alias="VALKEY_CONNECTION_TIMEOUT_MS",
    )
    key_prefix: str = Field(
        default="valkey-examples:flask-base:v1",
        pattern=r"^[a-z0-9][a-z0-9:._-]{0,127}$",
        validation_alias="VALKEY_KEY_PREFIX",
    )

    flask_host: str = Field(
        default="127.0.0.1",
        min_length=1,
        validation_alias="FLASK_HOST",
    )
    flask_port: int = Field(
        default=8000,
        ge=1,
        le=65_535,
        validation_alias="FLASK_PORT",
    )
    flask_threads: int = Field(
        default=4,
        ge=1,
        le=64,
        validation_alias="FLASK_THREADS",
    )

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    otel_enabled: bool = Field(
        default=True,
        validation_alias="OTEL_ENABLED",
    )
    otel_service_name: str = Field(
        default="valkey-flask-demo",
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$",
        validation_alias="OTEL_SERVICE_NAME",
    )
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    @model_validator(mode="after")
    def validate_topology_settings(self) -> Self:
        self.addresses()
        if self.topology is Topology.CLUSTER and self.database_id != 0:
            raise ValueError("Valkey Cluster supports only database 0")
        if self.otel_exporter_otlp_endpoint is not None:
            endpoint = self.otel_exporter_otlp_endpoint
            if not endpoint.startswith(("http://", "https://")):
                raise ValueError(
                    "OTEL_EXPORTER_OTLP_ENDPOINT must use http:// or https://"
                )
        return self

    def addresses(self) -> tuple[Address, ...]:
        """Parse and validate comma-separated host:port addresses."""

        raw_addresses = [
            item.strip()
            for item in self.valkey_addresses.split(",")
        ]
        if not raw_addresses or any(not item for item in raw_addresses):
            raise ValueError(
                "VALKEY_ADDRESSES must contain host:port entries"
            )
        if len(raw_addresses) > 32:
            raise ValueError(
                "VALKEY_ADDRESSES supports at most 32 entries"
            )
        return tuple(
            self._parse_address(item)
            for item in raw_addresses
        )

    @staticmethod
    def _parse_address(value: str) -> Address:
        if value.startswith("["):
            closing = value.find("]")
            if closing < 2 or value[closing + 1 : closing + 2] != ":":
                raise ValueError(f"Invalid bracketed address: {value}")
            host = value[1:closing]
            port_text = value[closing + 2 :]
        else:
            host, separator, port_text = value.rpartition(":")
            if not separator:
                raise ValueError(
                    f"Address must include a port: {value}"
                )

        if not host or any(character.isspace() for character in host):
            raise ValueError(f"Invalid address host: {value}")
        try:
            port = int(port_text)
        except ValueError as error:
            raise ValueError(f"Invalid address port: {value}") from error
        if not 1 <= port <= 65_535:
            raise ValueError(f"Address port is out of range: {value}")
        return host, port
```

### 10.2 Complete `models.py`

Create `src/valkey_flask_demo/models.py`:

```python
"""Pydantic response models shared by routes and tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from valkey_flask_demo.config import Topology


class CounterSnapshot(BaseModel):
    """Current value of one validated demo counter."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    value: int = Field(ge=0)
    topology: Topology


class TopologySnapshot(BaseModel):
    """Safe connection details suitable for an HTTP response."""

    model_config = ConfigDict(frozen=True)

    topology: Topology
    configured_addresses: tuple[str, ...]
    client: str
    sentinel_master: str | None = None
    discovered_primary: str | None = None
```

### 10.3 Complete `store.py`

Create `src/valkey_flask_demo/store.py`:

```python
"""Topology-aware Valkey access behind a small counter-store interface."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from threading import RLock
from typing import Protocol, TypeVar

from glide_sync import (
    AdvancedGlideClientConfiguration,
    AdvancedGlideClusterClientConfiguration,
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    GlideError,
    NodeAddress,
    NodeDiscoveryMode,
    ProtocolVersion,
)

from valkey_flask_demo.config import Address, AppSettings, Topology
from valkey_flask_demo.models import TopologySnapshot

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")
type DataClient = GlideClient | GlideClusterClient


class CounterStore(Protocol):
    """Interface consumed by the Flask adapter."""

    def get(self, name: str) -> int: ...

    def increment(self, name: str) -> int: ...

    def delete(self, name: str) -> bool: ...

    def ping(self) -> None: ...

    def topology_snapshot(self) -> TopologySnapshot: ...

    def close(self) -> None: ...


class ValkeyUnavailable(RuntimeError):
    """The selected Valkey topology could not complete an operation."""


class ValkeyStore:
    """Own one GLIDE client and hide topology-specific behavior."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._sentinel_lock = RLock()
        self._discovered_primary: Address | None = None
        self._client = self._connect()

    def get(self, name: str) -> int:
        value = self._run(
            lambda client: client.get(self._counter_key(name))
        )
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise ValkeyUnavailable(
                "Counter value is not an integer"
            ) from error

    def increment(self, name: str) -> int:
        return self._run(
            lambda client: client.incr(self._counter_key(name))
        )

    def delete(self, name: str) -> bool:
        deleted = self._run(
            lambda client: client.delete([self._counter_key(name)])
        )
        return deleted > 0

    def ping(self) -> None:
        response = self._run(lambda client: client.ping())
        if response != b"PONG":
            raise ValkeyUnavailable(
                "Valkey returned an unexpected PING response"
            )

    def topology_snapshot(self) -> TopologySnapshot:
        primary = (
            self._format_address(self._discovered_primary)
            if self._discovered_primary is not None
            else None
        )
        client_name = (
            "GlideClusterClient"
            if self._settings.topology is Topology.CLUSTER
            else "GlideClient"
        )
        return TopologySnapshot(
            topology=self._settings.topology,
            configured_addresses=tuple(
                self._format_address(address)
                for address in self._settings.addresses()
            ),
            client=client_name,
            sentinel_master=(
                self._settings.sentinel_master
                if self._settings.topology is Topology.SENTINEL
                else None
            ),
            discovered_primary=primary,
        )

    def close(self) -> None:
        self._client.close()

    def _run(self, operation: Callable[[DataClient], T]) -> T:
        if self._settings.topology is not Topology.SENTINEL:
            try:
                return operation(self._client)
            except GlideError as error:
                raise ValkeyUnavailable(
                    "Valkey operation failed"
                ) from error

        with self._sentinel_lock:
            try:
                return operation(self._client)
            except GlideError as first_error:
                LOGGER.warning(
                    "Sentinel-backed command failed; "
                    "rediscovering the primary",
                    extra={"topology": Topology.SENTINEL.value},
                    exc_info=first_error,
                )
                self._replace_sentinel_client()
                try:
                    return operation(self._client)
                except GlideError as retry_error:
                    raise ValkeyUnavailable(
                        "Sentinel-backed Valkey operation failed "
                        "after rediscovery"
                    ) from retry_error

    def _connect(self) -> DataClient:
        if self._settings.topology is Topology.CLUSTER:
            return GlideClusterClient.create(
                GlideClusterClientConfiguration(
                    addresses=self._node_addresses(
                        self._settings.addresses()
                    ),
                    request_timeout=self._settings.request_timeout_ms,
                    client_name=self._settings.otel_service_name,
                    advanced_config=(
                        AdvancedGlideClusterClientConfiguration(
                            connection_timeout=(
                                self._settings.connection_timeout_ms
                            )
                        )
                    ),
                )
            )

        if self._settings.topology is Topology.SENTINEL:
            primary = self._discover_sentinel_primary()
            self._discovered_primary = primary
            return self._create_standalone_client(
                [primary],
                static=True,
            )

        return self._create_standalone_client(
            list(self._settings.addresses()),
            static=False,
        )

    def _create_standalone_client(
        self,
        addresses: list[Address],
        *,
        static: bool,
    ) -> GlideClient:
        return GlideClient.create(
            GlideClientConfiguration(
                addresses=self._node_addresses(addresses),
                request_timeout=self._settings.request_timeout_ms,
                database_id=self._settings.database_id,
                client_name=self._settings.otel_service_name,
                node_discovery_mode=(
                    NodeDiscoveryMode.STATIC
                    if static
                    else NodeDiscoveryMode.STANDARD
                ),
                advanced_config=AdvancedGlideClientConfiguration(
                    connection_timeout=(
                        self._settings.connection_timeout_ms
                    )
                ),
            )
        )

    def _replace_sentinel_client(self) -> None:
        old_client = self._client
        primary = self._discover_sentinel_primary()
        replacement = self._create_standalone_client(
            [primary],
            static=True,
        )
        self._client = replacement
        self._discovered_primary = primary
        old_client.close()

    def _discover_sentinel_primary(self) -> Address:
        errors: list[str] = []
        for sentinel in self._settings.addresses():
            client: GlideClient | None = None
            try:
                client = GlideClient.create(
                    GlideClientConfiguration(
                        addresses=self._node_addresses([sentinel]),
                        request_timeout=(
                            self._settings.request_timeout_ms
                        ),
                        protocol=ProtocolVersion.RESP2,
                        node_discovery_mode=NodeDiscoveryMode.STATIC,
                        advanced_config=(
                            AdvancedGlideClientConfiguration(
                                connection_timeout=(
                                    self._settings.connection_timeout_ms
                                )
                            )
                        ),
                    )
                )
                response = client.custom_command(
                    [
                        "SENTINEL",
                        "GET-MASTER-ADDR-BY-NAME",
                        self._settings.sentinel_master,
                    ]
                )
                primary = self._parse_sentinel_response(response)
                LOGGER.info(
                    "Discovered Sentinel primary",
                    extra={
                        "topology": Topology.SENTINEL.value,
                        "sentinel": self._format_address(sentinel),
                        "primary": self._format_address(primary),
                    },
                )
                return primary
            except (GlideError, ValueError) as error:
                errors.append(
                    f"{self._format_address(sentinel)}: {error}"
                )
            finally:
                if client is not None:
                    client.close()

        detail = (
            "; ".join(errors)
            if errors
            else "no Sentinel addresses were configured"
        )
        raise ValkeyUnavailable(
            f"Sentinel could not discover a primary: {detail}"
        )

    @staticmethod
    def _parse_sentinel_response(response: object) -> Address:
        if (
            not isinstance(response, Sequence)
            or isinstance(response, (str, bytes, bytearray))
            or len(response) != 2
        ):
            raise ValueError(
                "Sentinel returned an invalid primary address"
            )

        host = ValkeyStore._decode(response[0])
        port_text = ValkeyStore._decode(response[1])
        if not host:
            raise ValueError(
                "Sentinel returned an empty primary host"
            )
        try:
            port = int(port_text)
        except ValueError as error:
            raise ValueError(
                "Sentinel returned an invalid primary port"
            ) from error
        if not 1 <= port <= 65_535:
            raise ValueError(
                "Sentinel returned an out-of-range primary port"
            )
        return host, port

    @staticmethod
    def _decode(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, str):
            return value
        raise ValueError(
            "Valkey returned a non-text address field"
        )

    def _counter_key(self, name: str) -> str:
        return f"{self._settings.key_prefix}:counter:{name}"

    @staticmethod
    def _node_addresses(
        addresses: Sequence[Address],
    ) -> list[NodeAddress]:
        return [
            NodeAddress(host, port)
            for host, port in addresses
        ]

    @staticmethod
    def _format_address(address: Address) -> str:
        host, port = address
        rendered_host = f"[{host}]" if ":" in host else host
        return f"{rendered_host}:{port}"
```

The Sentinel path has two client lifetimes: a short-lived discovery client and
the process-lifetime data client. The one-retry `_run()` path serializes
replacement with an `RLock`.

### 10.4 Complete `telemetry.py`

Create `src/valkey_flask_demo/telemetry.py`:

```python
"""Structured logging and OpenTelemetry setup."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from flask import Flask
from glide_sync import OpenTelemetry as GlideOpenTelemetry
from glide_sync import (
    OpenTelemetryConfig as GlideOpenTelemetryConfig,
)
from glide_sync import (
    OpenTelemetryTracesConfig as GlideOpenTelemetryTracesConfig,
)
from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from valkey_flask_demo.config import AppSettings

_CONFIGURE_LOCK = Lock()
_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    """JSON formatter preserving OpenTelemetry correlation fields."""

    _extra_fields = (
        "topology",
        "operation",
        "sentinel",
        "primary",
        "request_id",
        "duration_ms",
        "status_code",
    )

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(
                record,
                "trace_id",
                getattr(record, "otelTraceID", "0"),
            ),
            "span_id": getattr(
                record,
                "span_id",
                getattr(record, "otelSpanID", "0"),
            ),
            "service_name": self._service_name,
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )
        return json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
        )


def configure_observability(settings: AppSettings) -> None:
    """Configure process-wide logging and optional OTLP export once."""

    global _CONFIGURED
    with _CONFIGURE_LOCK:
        if _CONFIGURED:
            return

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(settings.log_level)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            JsonLogFormatter(settings.otel_service_name)
        )
        root_logger.addHandler(stream_handler)

        if settings.otel_enabled:
            LoggingInstrumentor().instrument(
                set_logging_format=False
            )
            resource = Resource.create(
                {
                    "service.name": settings.otel_service_name,
                    "deployment.environment.name": "local-demo",
                    "valkey.topology": settings.topology.value,
                }
            )
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            endpoint = settings.otel_exporter_otlp_endpoint
            if endpoint:
                base_endpoint = endpoint.rstrip("/")
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(
                        OTLPSpanExporter(
                            endpoint=(
                                f"{base_endpoint}/v1/traces"
                            )
                        )
                    )
                )

                logger_provider = LoggerProvider(
                    resource=resource
                )
                logger_provider.add_log_record_processor(
                    BatchLogRecordProcessor(
                        OTLPLogExporter(
                            endpoint=f"{base_endpoint}/v1/logs"
                        )
                    )
                )
                _logs.set_logger_provider(logger_provider)
                root_logger.addHandler(
                    LoggingHandler(
                        level=logging.NOTSET,
                        logger_provider=logger_provider,
                    )
                )

                if not GlideOpenTelemetry.is_initialized():
                    GlideOpenTelemetry.init(
                        GlideOpenTelemetryConfig(
                            traces=GlideOpenTelemetryTracesConfig(
                                endpoint=(
                                    f"{base_endpoint}/v1/traces"
                                ),
                                sample_percentage=100,
                            )
                        )
                    )

        _CONFIGURED = True


def instrument_flask(app: Flask, settings: AppSettings) -> None:
    """Attach Flask request spans when observability is enabled."""

    if settings.otel_enabled:
        FlaskInstrumentor().instrument_app(
            app
        )  # type: ignore[no-untyped-call]
```

### 10.5 Complete `app.py`

Create `src/valkey_flask_demo/app.py`:

```python
"""Flask application factory and HTTP adapter."""

from __future__ import annotations

import atexit
import logging
import time
import uuid
from typing import Annotated, Any

from flask import Flask, Response, g, jsonify, request
from opentelemetry import trace
from pydantic import Field, TypeAdapter, ValidationError
from waitress import serve  # type: ignore[import-untyped]

from valkey_flask_demo.config import AppSettings
from valkey_flask_demo.models import CounterSnapshot
from valkey_flask_demo.store import (
    CounterStore,
    ValkeyStore,
    ValkeyUnavailable,
)
from valkey_flask_demo.telemetry import (
    configure_observability,
    instrument_flask,
)

LOGGER = logging.getLogger(__name__)
COUNTER_NAME: TypeAdapter[str] = TypeAdapter(
    Annotated[
        str,
        Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$"),
    ]
)


class FlaskDemo:
    """Own route registration and translate the store to HTTP."""

    def __init__(
        self,
        settings: AppSettings,
        store: CounterStore,
    ) -> None:
        self.settings = settings
        self.store = store
        self.app = Flask(__name__)
        self.app.config["JSON_SORT_KEYS"] = True
        self.app.extensions["counter_store"] = store
        instrument_flask(self.app, settings)
        self._register_hooks()
        self._register_routes()
        self._register_error_handlers()

    def _register_hooks(self) -> None:
        @self.app.before_request
        def begin_request() -> None:
            span_context = (
                trace.get_current_span().get_span_context()
            )
            g.request_id = (
                request.headers.get("X-Request-ID")
                or uuid.uuid7().hex
            )
            g.started_at = time.monotonic()
            g.trace_id = (
                f"{span_context.trace_id:032x}"
                if span_context.is_valid
                else "0"
            )
            g.span_id = (
                f"{span_context.span_id:016x}"
                if span_context.is_valid
                else "0"
            )

        @self.app.after_request
        def finish_request(response: Response) -> Response:
            duration_ms = round(
                (time.monotonic() - g.started_at) * 1_000,
                2,
            )
            response.headers["X-Request-ID"] = g.request_id
            LOGGER.info(
                "HTTP request completed",
                extra={
                    "request_id": g.request_id,
                    "trace_id": g.trace_id,
                    "span_id": g.span_id,
                    "topology": self.settings.topology.value,
                    "operation": (
                        f"{request.method} {request.path}"
                    ),
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                },
            )
            return response

    def _register_routes(self) -> None:
        self.app.add_url_rule(
            "/",
            view_func=self.index,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/health/live",
            view_func=self.live,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/health/ready",
            view_func=self.ready,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/topology",
            view_func=self.topology,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/counters/<name>",
            view_func=self.counter,
            methods=["GET", "POST", "DELETE"],
        )

    def _register_error_handlers(self) -> None:
        @self.app.errorhandler(ValidationError)
        def invalid_input(
            error: ValidationError,
        ) -> tuple[Response, int]:
            LOGGER.info(
                "Request validation failed",
                extra={"request_id": g.request_id},
            )
            return jsonify(
                {
                    "error": (
                        "counter name must match "
                        "[a-z0-9][a-z0-9_-]{0,63}"
                    )
                }
            ), 400

        @self.app.errorhandler(ValkeyUnavailable)
        def dependency_unavailable(
            error: ValkeyUnavailable,
        ) -> tuple[Response, int]:
            LOGGER.exception(
                "Valkey dependency unavailable",
                extra={
                    "request_id": g.request_id,
                    "topology": self.settings.topology.value,
                },
            )
            return jsonify(
                {"error": "Valkey dependency unavailable"}
            ), 503

    def index(self) -> tuple[Response, int]:
        body: dict[str, Any] = {
            "application": "valkey-topology-aware-flask-demo",
            "topology": self.settings.topology.value,
            "endpoints": {
                "topology": "/api/topology",
                "counter": "/api/counters/<name>",
                "readiness": "/health/ready",
            },
        }
        return jsonify(body), 200

    def live(self) -> tuple[Response, int]:
        return jsonify({"status": "live"}), 200

    def ready(self) -> tuple[Response, int]:
        self.store.ping()
        return jsonify(
            {
                "status": "ready",
                "topology": self.settings.topology.value,
            }
        ), 200

    def topology(self) -> tuple[Response, int]:
        snapshot = self.store.topology_snapshot()
        return jsonify(
            snapshot.model_dump(mode="json")
        ), 200

    def counter(self, name: str) -> tuple[Response, int]:
        validated_name = COUNTER_NAME.validate_python(name)
        if request.method == "POST":
            value = self.store.increment(validated_name)
        elif request.method == "DELETE":
            self.store.delete(validated_name)
            value = 0
        else:
            value = self.store.get(validated_name)

        snapshot = CounterSnapshot(
            name=validated_name,
            value=value,
            topology=self.settings.topology,
        )
        return jsonify(
            snapshot.model_dump(mode="json")
        ), 200


def create_app(
    settings: AppSettings | None = None,
    store: CounterStore | None = None,
) -> Flask:
    """Create a configured Flask app with an injectable store."""

    runtime_settings = settings or AppSettings()
    configure_observability(runtime_settings)
    runtime_store = store or ValkeyStore(runtime_settings)
    demo = FlaskDemo(runtime_settings, runtime_store)
    return demo.app


def main() -> None:
    """Run the application with a local WSGI server."""

    settings = AppSettings()
    app = create_app(settings)
    store = app.extensions["counter_store"]
    atexit.register(store.close)
    LOGGER.info(
        "Starting Flask demo",
        extra={
            "topology": settings.topology.value,
            "operation": "startup",
        },
    )
    serve(
        app,
        host=settings.flask_host,
        port=settings.flask_port,
        threads=settings.flask_threads,
    )


if __name__ == "__main__":
    main()
```

Review and statically check the completed application:

```shell
bat --paging=never --style=numbers src/valkey_flask_demo/config.py
bat --paging=never --style=numbers src/valkey_flask_demo/store.py
bat --paging=never --style=numbers src/valkey_flask_demo/telemetry.py
bat --paging=never --style=numbers src/valkey_flask_demo/app.py
uv run ruff check src
uv run mypy
```

## 11. Add local environment files

Create `.env.example`. The values describe the default standalone profile, and
the comments show how to select another topology:

```dotenv
# Select the Compose profile through make:
#   TOPOLOGY=standalone make start
#   TOPOLOGY=sentinel make start
#   TOPOLOGY=cluster make start
VALKEY_TOPOLOGY=standalone
VALKEY_ADDRESSES=standalone:6379
VALKEY_SENTINEL_MASTER=demo-primary
VALKEY_DATABASE_ID=0
VALKEY_REQUEST_TIMEOUT_MS=1000
VALKEY_CONNECTION_TIMEOUT_MS=2000
VALKEY_KEY_PREFIX=valkey-examples:flask-base:v1

FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_THREADS=4

LOG_LEVEL=INFO
OTEL_ENABLED=true
OTEL_SERVICE_NAME=valkey-flask-demo
# Optional base URL. The application appends /v1/traces and /v1/logs.
# OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

Copy it for local use:

```shell
cp .env.example .env
```

The Compose services override the topology-specific addresses, so `.env`
remains useful for shared settings such as ports, timeouts, log level, and the
key prefix.

Create `.gitignore`:

```gitignore
.cache/
.coverage
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
.runtime/
.venv/
__pycache__/
coverage.xml
htmlcov/
*.egg-info/
*.pyc
```

Create `.dockerignore`:

```gitignore
.cache
.coverage
.env
.git
.mypy_cache
.pytest_cache
.ruff_cache
.runtime
.venv
__pycache__
htmlcov
*.egg-info
*.pyc
```

The two ignore files have different purposes:

- `.gitignore` prevents local state and secrets from entering a commit.
- `.dockerignore` keeps those same files out of the Docker build context.

Review the files before continuing:

```shell
bat --paging=never --style=numbers .env.example
bat --paging=never --style=numbers .gitignore
bat --paging=never --style=numbers .dockerignore
```

## 12. Create Docker and Compose

This section builds the complete local environment. It contains the Flask
container plus independent standalone, Sentinel, and cluster profiles.

### 12.1 Create the application image

Create `Dockerfile`:

```dockerfile
FROM python:3.14.7-slim-trixie@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN python -m pip install --no-cache-dir uv==0.12.5 \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app

WORKDIR /app

COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --frozen --no-install-project

COPY src ./src
COPY tests ./tests
RUN uv sync --frozen \
    && rm -rf /tmp/uv-cache

RUN chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["uv", "run", "--frozen"]
CMD ["valkey-flask-demo"]
```

The order is intentional:

1. The base image and uv version are pinned for repeatable recordings.
2. Dependency files are copied before application source so Docker can reuse
   the expensive dependency layer after ordinary code edits.
3. The first `uv sync` installs locked dependencies without installing the
   project.
4. The second `uv sync` installs the project after `src/` is available.
5. The process runs as the unprivileged `app` user.
6. `ENTRYPOINT` provides the locked uv environment and `CMD` supplies the
   application command. Compose can replace `CMD` when it runs tests.

Inspect the result:

```shell
bat --paging=never --style=numbers Dockerfile
```

### 12.2 Create the Sentinel configuration

Create the directory:

```shell
mkdir -p infra/sentinel
```

Create `infra/sentinel/sentinel.conf`:

```text
port 26379
bind 0.0.0.0
protected-mode no
dir /tmp

sentinel resolve-hostnames yes
sentinel announce-hostnames yes
sentinel monitor demo-primary sentinel-primary 6379 2
sentinel down-after-milliseconds demo-primary 1500
sentinel failover-timeout demo-primary 10000
sentinel parallel-syncs demo-primary 1
```

The important values are:

- `demo-primary`, which must match `VALKEY_SENTINEL_MASTER`;
- `sentinel-primary`, the Compose DNS name of the monitored primary;
- quorum `2`, so two of the three Sentinel processes must agree; and
- hostname resolution, which lets the containers discover one another by
  Compose service name.

Sentinel rewrites its configuration while running. The Compose file therefore
mounts this source read-only, copies it to `/tmp`, and starts Sentinel from the
writable copy.

### 12.3 Create the Compose stack

Create `compose.yaml`:

```yaml
name: valkey-example-topology-aware-python-flask

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

x-app: &app
  build:
    context: .
    dockerfile: Dockerfile
  image: valkey-example-topology-aware-python-flask:local
  restart: "no"
  init: true
  networks:
    - demo
  security_opt:
    - no-new-privileges:true
  env_file:
    - path: .env
      required: false
  environment:
    FLASK_HOST: 0.0.0.0
    FLASK_PORT: ${FLASK_PORT:-8000}
    FLASK_THREADS: ${FLASK_THREADS:-4}
    LOG_LEVEL: ${LOG_LEVEL:-INFO}
    OTEL_ENABLED: ${OTEL_ENABLED:-true}
    OTEL_SERVICE_NAME: ${OTEL_SERVICE_NAME:-valkey-flask-demo}
    VALKEY_CONNECTION_TIMEOUT_MS: ${VALKEY_CONNECTION_TIMEOUT_MS:-2000}
    VALKEY_DATABASE_ID: "0"
    VALKEY_KEY_PREFIX: ${VALKEY_KEY_PREFIX:-valkey-examples:flask-base:v1}
    VALKEY_REQUEST_TIMEOUT_MS: ${VALKEY_REQUEST_TIMEOUT_MS:-1000}
  ports:
    - 127.0.0.1:${FLASK_PORT:-8000}:${FLASK_PORT:-8000}
  healthcheck:
    test:
      - CMD
      - python
      - -c
      - >-
        import os, urllib.request;
        urllib.request.urlopen(
        f"http://127.0.0.1:{os.environ['FLASK_PORT']}/health/ready",
        timeout=2)
    interval: 1s
    timeout: 3s
    retries: 60
    start_period: 3s

services:
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

  app-standalone:
    <<: *app
    profiles: ["standalone"]
    environment:
      FLASK_HOST: 0.0.0.0
      FLASK_PORT: ${FLASK_PORT:-8000}
      FLASK_THREADS: ${FLASK_THREADS:-4}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      OTEL_ENABLED: ${OTEL_ENABLED:-true}
      OTEL_SERVICE_NAME: ${OTEL_SERVICE_NAME:-valkey-flask-demo}
      VALKEY_ADDRESSES: standalone:6379
      VALKEY_CONNECTION_TIMEOUT_MS: ${VALKEY_CONNECTION_TIMEOUT_MS:-2000}
      VALKEY_DATABASE_ID: "0"
      VALKEY_KEY_PREFIX: ${VALKEY_KEY_PREFIX:-valkey-examples:flask-base:v1}
      VALKEY_REQUEST_TIMEOUT_MS: ${VALKEY_REQUEST_TIMEOUT_MS:-1000}
      VALKEY_TOPOLOGY: standalone
    depends_on:
      standalone:
        condition: service_healthy

  sentinel-primary:
    <<: *valkey
    profiles: ["sentinel"]
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

  sentinel-replica:
    <<: *valkey
    profiles: ["sentinel"]
    command:
      - valkey-server
      - --appendonly
      - "no"
      - --save
      - ""
      - --protected-mode
      - "no"
      - --replicaof
      - sentinel-primary
      - "6379"
    tmpfs:
      - /data
    depends_on:
      sentinel-primary:
        condition: service_healthy

  sentinel-1:
    image: valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9
    profiles: ["sentinel"]
    restart: "no"
    command:
      - /bin/sh
      - -c
      - cp /etc/valkey/sentinel.conf /tmp/sentinel.conf && exec valkey-sentinel /tmp/sentinel.conf
    volumes:
      - ./infra/sentinel/sentinel.conf:/etc/valkey/sentinel.conf:ro
    tmpfs:
      - /tmp
    networks:
      - demo
    security_opt:
      - no-new-privileges:true
    healthcheck: &sentinel-healthcheck
      test: ["CMD", "valkey-cli", "-h", "127.0.0.1", "-p", "26379", "ping"]
      interval: 1s
      timeout: 1s
      retries: 30
      start_period: 2s
    depends_on: &sentinel-dependencies
      sentinel-primary:
        condition: service_healthy
      sentinel-replica:
        condition: service_healthy

  sentinel-2:
    image: valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9
    profiles: ["sentinel"]
    restart: "no"
    command:
      - /bin/sh
      - -c
      - cp /etc/valkey/sentinel.conf /tmp/sentinel.conf && exec valkey-sentinel /tmp/sentinel.conf
    volumes:
      - ./infra/sentinel/sentinel.conf:/etc/valkey/sentinel.conf:ro
    tmpfs:
      - /tmp
    networks:
      - demo
    security_opt:
      - no-new-privileges:true
    healthcheck: *sentinel-healthcheck
    depends_on: *sentinel-dependencies

  sentinel-3:
    image: valkey/valkey:9.1.1-alpine@sha256:15568b9cb7eb67f4aed4de018c23f13d344e0e6437b31fe8fb8823dc81ebb3a9
    profiles: ["sentinel"]
    restart: "no"
    command:
      - /bin/sh
      - -c
      - cp /etc/valkey/sentinel.conf /tmp/sentinel.conf && exec valkey-sentinel /tmp/sentinel.conf
    volumes:
      - ./infra/sentinel/sentinel.conf:/etc/valkey/sentinel.conf:ro
    tmpfs:
      - /tmp
    networks:
      - demo
    security_opt:
      - no-new-privileges:true
    healthcheck: *sentinel-healthcheck
    depends_on: *sentinel-dependencies

  app-sentinel:
    <<: *app
    profiles: ["sentinel"]
    environment:
      FLASK_HOST: 0.0.0.0
      FLASK_PORT: ${FLASK_PORT:-8000}
      FLASK_THREADS: ${FLASK_THREADS:-4}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      OTEL_ENABLED: ${OTEL_ENABLED:-true}
      OTEL_SERVICE_NAME: ${OTEL_SERVICE_NAME:-valkey-flask-demo}
      VALKEY_ADDRESSES: sentinel-1:26379,sentinel-2:26379,sentinel-3:26379
      VALKEY_CONNECTION_TIMEOUT_MS: ${VALKEY_CONNECTION_TIMEOUT_MS:-2000}
      VALKEY_DATABASE_ID: "0"
      VALKEY_KEY_PREFIX: ${VALKEY_KEY_PREFIX:-valkey-examples:flask-base:v1}
      VALKEY_REQUEST_TIMEOUT_MS: ${VALKEY_REQUEST_TIMEOUT_MS:-1000}
      VALKEY_SENTINEL_MASTER: demo-primary
      VALKEY_TOPOLOGY: sentinel
    depends_on:
      sentinel-1:
        condition: service_healthy
      sentinel-2:
        condition: service_healthy
      sentinel-3:
        condition: service_healthy

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
    depends_on:
      cluster-node-1:
        condition: service_healthy
      cluster-node-2:
        condition: service_healthy
      cluster-node-3:
        condition: service_healthy

  app-cluster:
    <<: *app
    profiles: ["cluster"]
    environment:
      FLASK_HOST: 0.0.0.0
      FLASK_PORT: ${FLASK_PORT:-8000}
      FLASK_THREADS: ${FLASK_THREADS:-4}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      OTEL_ENABLED: ${OTEL_ENABLED:-true}
      OTEL_SERVICE_NAME: ${OTEL_SERVICE_NAME:-valkey-flask-demo}
      VALKEY_ADDRESSES: cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
      VALKEY_CONNECTION_TIMEOUT_MS: ${VALKEY_CONNECTION_TIMEOUT_MS:-2000}
      VALKEY_DATABASE_ID: "0"
      VALKEY_KEY_PREFIX: ${VALKEY_KEY_PREFIX:-valkey-examples:flask-base:v1}
      VALKEY_REQUEST_TIMEOUT_MS: ${VALKEY_REQUEST_TIMEOUT_MS:-1000}
      VALKEY_TOPOLOGY: cluster
    depends_on:
      cluster-init:
        condition: service_completed_successfully

networks:
  demo:
    driver: bridge
```

Read the file in five layers:

1. `x-valkey` centralizes the Valkey image, network, security setting, and
   health check.
2. `x-app` centralizes the Flask image, shared environment, loopback-only port,
   and application readiness check.
3. The `standalone` profile starts one Valkey process and one Flask process.
4. The `sentinel` profile starts a primary, replica, three Sentinel processes,
   and a Flask process configured with the three Sentinel addresses.
5. The `cluster` profile starts three shard nodes. The one-shot `cluster-init`
   service joins them before Flask starts.

No Valkey or Sentinel port is published to the host. Only Flask is exposed,
and it is bound to `127.0.0.1`.

Validate each profile before starting containers:

```shell
docker compose --profile standalone config --quiet
docker compose --profile sentinel config --quiet
docker compose --profile cluster config --quiet
yq '.services | keys' compose.yaml
bat --paging=never --style=numbers compose.yaml
```

If Compose reports a missing `.env`, create it from `.env.example`. The
`env_file` is optional, but having the file makes the tutorial easier to
follow and edit during a recording.

## 13. Add every lifecycle script

The scripts provide a small, repeatable command surface around Compose. Keep
application behavior in Python modules and orchestration behavior here.

Create the scripts directory:

```shell
mkdir -p scripts
```

### 13.1 Add shared shell helpers

Create `scripts/common.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"

read_dotenv_value() {
  local name="$1"
  local line
  local value

  [[ -f .env ]] || return 1
  line="$(awk -F= -v key="$name" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' .env)"
  [[ -n "$line" ]] || return 1
  value="${line%$'\r'}"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s\n' "$value"
}

dotenv_topology="$(read_dotenv_value VALKEY_TOPOLOGY || true)"
dotenv_port="$(read_dotenv_value FLASK_PORT || true)"

export TOPOLOGY="${TOPOLOGY:-${dotenv_topology:-standalone}}"
export FLASK_PORT="${FLASK_PORT:-${dotenv_port:-8000}}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:${FLASK_PORT}}"

case "$TOPOLOGY" in
  standalone | sentinel | cluster)
    ;;
  *)
    printf 'TOPOLOGY must be standalone, sentinel, or cluster; received %s\n' \
      "$TOPOLOGY" >&2
    exit 2
    ;;
esac

app_service() {
  printf 'app-%s\n' "$TOPOLOGY"
}

compose() {
  docker compose --profile "$TOPOLOGY" "$@"
}

compose_all() {
  docker compose \
    --profile standalone \
    --profile sentinel \
    --profile cluster \
    "$@"
}
```

This helper:

- changes to the capsule root, so scripts work from any current directory;
- keeps the uv cache inside the capsule;
- reads topology and port defaults from `.env`;
- lets explicit shell variables override `.env`;
- rejects unknown topology names; and
- exposes one Compose function for the selected profile and another for
  cleaning every profile.

### 13.2 Start the selected profile

Create `scripts/start.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if ! compose up -d --build --wait "$(app_service)"; then
  printf 'Startup failed for topology %s. Recent application logs:\n' "$TOPOLOGY" >&2
  compose logs --no-color --tail=100 "$(app_service)" >&2 || true
  exit 1
fi

uv run --frozen python scripts/wait_for_http.py \
  "${BASE_URL}/health/ready" \
  --timeout 60

printf 'Flask and Valkey are ready: topology=%s url=%s\n' "$TOPOLOGY" "$BASE_URL"
```

`docker compose --wait` waits for Compose health checks. The extra HTTP wait
verifies the same readiness route that a user will call during the demo. On
failure, the script prints the latest application logs before exiting.

### 13.3 Wait for the HTTP application

Create `scripts/wait_for_http.py`:

```python
#!/usr/bin/env python3
"""Wait until an HTTP endpoint returns a successful status."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    deadline = time.monotonic() + args.timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(args.url, timeout=2) as response:
                if 200 <= response.status < 300:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        time.sleep(0.25)

    raise SystemExit(f"Timed out waiting for {args.url}: {last_error}")


if __name__ == "__main__":
    main()
```

This script deliberately uses the Python standard library. It can run as soon
as the locked environment exists and needs no separate command-line utility.

### 13.4 Add the automated demo journey

Create `scripts/demo.py`:

```python
#!/usr/bin/env python3
"""Run the visible HTTP demo journey."""

from __future__ import annotations

import os

import httpx


def main() -> None:
    port = os.getenv("FLASK_PORT", "8000")
    base_url = os.getenv(
        "BASE_URL",
        f"http://127.0.0.1:{port}",
    )
    expected_topology = os.getenv(
        "TOPOLOGY",
        "standalone",
    )

    with httpx.Client(
        base_url=base_url,
        timeout=5,
    ) as client:
        topology = client.get("/api/topology")
        topology.raise_for_status()
        topology_body = topology.json()
        if topology_body["topology"] != expected_topology:
            raise SystemExit(
                "Expected topology "
                f"{expected_topology}; received "
                f"{topology_body['topology']}"
            )

        client.delete(
            "/api/counters/demo"
        ).raise_for_status()
        first = client.post("/api/counters/demo")
        first.raise_for_status()
        second = client.post("/api/counters/demo")
        second.raise_for_status()
        current = client.get("/api/counters/demo")
        current.raise_for_status()

        print(f"Topology: {topology_body['topology']}")
        print(f"GLIDE client: {topology_body['client']}")
        if topology_body.get("discovered_primary"):
            print(
                "Sentinel primary: "
                f"{topology_body['discovered_primary']}"
            )
        print(
            "Counter values: "
            f"{first.json()['value']} -> "
            f"{second.json()['value']}"
        )
        print(f"Stored value: {current.json()['value']}")


if __name__ == "__main__":
    main()
```

The script confirms the requested topology before changing data. It then
deletes the known demo counter, increments twice, reads it, and prints the
selected GLIDE client. Sentinel adds the discovered primary address.

### 13.5 Add a narrowly scoped reset

Create `scripts/reset.py`:

```python
#!/usr/bin/env python3
"""Delete only the capsule's known demo counter."""

from __future__ import annotations

import os

import httpx


def main() -> None:
    port = os.getenv("FLASK_PORT", "8000")
    base_url = os.getenv(
        "BASE_URL",
        f"http://127.0.0.1:{port}",
    )
    response = httpx.delete(
        f"{base_url}/api/counters/demo",
        timeout=5,
    )
    response.raise_for_status()
    print("Deleted the demo counter.")


if __name__ == "__main__":
    main()
```

Reset uses the public HTTP contract and deletes only the known `demo` key. It
does not flush the Valkey database.

### 13.6 Stop all resources owned by this capsule

Create `scripts/stop.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_all down --remove-orphans --volumes
printf 'Stopped resources owned by topology-aware-python-flask.\n'
```

The Compose project has a fixed name at the top of `compose.yaml`.
`compose_all` activates all profiles before `down`, allowing one command to
remove resources left by any previously selected topology.

### 13.7 Test every real topology

Create `scripts/test-real.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

cleanup() {
  docker compose \
    --profile standalone \
    --profile sentinel \
    --profile cluster \
    down --remove-orphans --volumes >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for topology in standalone sentinel cluster; do
  test_port="$(
    uv run --frozen python -c \
      'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
  )"
  base_url="http://127.0.0.1:${test_port}"

  printf '\n== Verify %s topology ==\n' "$topology"
  cleanup

  TOPOLOGY="$topology" \
    FLASK_PORT="$test_port" \
    ./scripts/start.sh

  TOPOLOGY="$topology" \
    FLASK_PORT="$test_port" \
    docker compose --profile "$topology" run \
      --rm \
      --no-deps \
      "app-$topology" \
      pytest tests/integration

  BASE_URL="$base_url" \
    EXPECTED_TOPOLOGY="$topology" \
    uv run --frozen pytest tests/journey

  TOPOLOGY="$topology" \
    FLASK_PORT="$test_port" \
    ./scripts/stop.sh
done
```

The real test script:

1. installs a trap so interrupted runs still clean up;
2. asks the operating system for an available loopback port;
3. starts one topology;
4. runs store integration tests inside the application image;
5. runs HTTP journey tests from the host; and
6. stops that topology before moving to the next one.

Mark the shell scripts executable:

```shell
chmod +x \
  scripts/common.sh \
  scripts/start.sh \
  scripts/stop.sh \
  scripts/test-real.sh
```

Review and statically check all scripts:

```shell
bat --paging=never --style=numbers scripts/common.sh
bat --paging=never --style=numbers scripts/start.sh
bat --paging=never --style=numbers scripts/wait_for_http.py
bat --paging=never --style=numbers scripts/demo.py
bat --paging=never --style=numbers scripts/reset.py
bat --paging=never --style=numbers scripts/stop.sh
bat --paging=never --style=numbers scripts/test-real.sh
shellcheck -x scripts/*.sh
uv run ruff check scripts
```

## 14. Add the complete Make interface

Create `Makefile`:

<!-- markdownlint-disable MD010 -->

```makefile
SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start stop reset demo format lint typecheck test-unit \
	test-real verify-static verify clean

help:
	@printf '%s\n' \
		"setup        Install the locked Python environment" \
		"start        Start TOPOLOGY=standalone|sentinel|cluster (default: standalone)" \
		"stop         Stop only this capsule's Compose resources" \
		"reset        Delete the known demo counter through the application" \
		"demo         Exercise topology reporting and the demo counter" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run integration and HTTP journeys against all topologies" \
		"verify       Run all static, unit, integration, and journey checks"

setup:
	uv sync --frozen

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

reset:
	uv run --frozen python scripts/reset.py

demo:
	uv run --frozen python scripts/demo.py

format:
	uv run --frozen ruff format src tests scripts
	uv run --frozen ruff check --fix src tests scripts

lint:
	uv run --frozen ruff format --check src tests scripts
	uv run --frozen ruff check src tests scripts
	shellcheck -x scripts/*.sh

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest tests/unit --cov --cov-report=term-missing

test-real:
	./scripts/test-real.sh

verify-static: lint typecheck
	docker compose config --quiet
	../../../tools/ci/check-structure.sh

verify: setup verify-static test-unit test-real

clean: stop
	rm -rf .cache .coverage .mypy_cache .pytest_cache .ruff_cache .runtime .venv \
		htmlcov src/*.egg-info
```

<!-- markdownlint-enable MD010 -->

The Makefile is intentionally thin. Each target delegates to uv, Compose, or a
script that can also be run directly. `UV_CACHE_DIR` stays inside the capsule,
which is useful in restricted shells and makes cleanup predictable.

Inspect the target list:

```shell
make help
bat --paging=never --style=numbers Makefile
```

## 15. Add tests in layers

Create the test directories:

```shell
mkdir -p tests/unit tests/integration tests/journey
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/journey/__init__.py
```

Write the tests in this order:

1. `tests/unit/test_config.py` covers address parsing and invalid topology
   combinations.
2. `tests/unit/test_store.py` covers GLIDE client selection, byte decoding,
   Sentinel discovery responses, and retry behavior.
3. `tests/unit/test_app.py` injects a fake store and tests routes without
   starting Valkey.
4. `tests/integration/test_store.py` runs the same store contract against each
   real profile.
5. `tests/journey/test_http_journey.py` calls the running Flask process and
   checks topology reporting plus counter behavior.

Display each finished test file during a recording:

```shell
bat --paging=never --style=numbers tests/unit/test_config.py
bat --paging=never --style=numbers tests/unit/test_store.py
bat --paging=never --style=numbers tests/unit/test_app.py
bat --paging=never --style=numbers tests/integration/test_store.py
bat --paging=never --style=numbers tests/journey/test_http_journey.py
```

Run the fast feedback loop before starting Docker:

```shell
make lint
make typecheck
make test-unit
```

Then validate Compose and the repository capsule structure:

```shell
make verify-static
```

## 16. Run the finished capsule

### 16.1 Start standalone

```shell
make setup
TOPOLOGY=standalone make start
```

Inspect the running services:

```shell
docker compose --profile standalone ps
docker compose --profile standalone logs --tail=50 app-standalone
```

Use HTTPie for the visible interaction:

```shell
http --ignore-stdin GET :8000/api/topology
http --ignore-stdin DELETE :8000/api/counters/demo
http --ignore-stdin POST :8000/api/counters/demo
http --ignore-stdin POST :8000/api/counters/demo
http --ignore-stdin GET :8000/api/counters/demo
```

The curl equivalents pipe JSON through `jq`:

```shell
curl --fail --silent --show-error http://127.0.0.1:8000/api/topology | jq
curl --fail --silent --show-error \
  --request POST \
  http://127.0.0.1:8000/api/counters/demo | jq
curl --fail --silent --show-error \
  http://127.0.0.1:8000/api/counters/demo | jq
```

Run the scripted journey and stop the profile:

```shell
TOPOLOGY=standalone make demo
TOPOLOGY=standalone make reset
TOPOLOGY=standalone make stop
```

### 16.2 Repeat with Sentinel

```shell
TOPOLOGY=sentinel make start
TOPOLOGY=sentinel make demo
http --ignore-stdin GET :8000/api/topology
TOPOLOGY=sentinel make stop
```

The topology response should show:

- topology `sentinel`;
- client `GlideClient`; and
- the primary address discovered through the `demo-primary` Sentinel group.

### 16.3 Repeat with cluster

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
http --ignore-stdin GET :8000/api/topology
TOPOLOGY=cluster make stop
```

The topology response should now show topology `cluster` and client
`GlideClusterClient`. The Flask routes remain unchanged.

### 16.4 Run complete verification

```shell
make verify
```

`make verify` runs static checks and unit tests, then starts all three
topologies one at a time for integration and HTTP journey tests.

The final video takeaway is simple: configuration chooses the connection
workflow, `ValkeyStore` hides those differences, and the Flask adapter uses the
same interface for standalone, Sentinel, and cluster.

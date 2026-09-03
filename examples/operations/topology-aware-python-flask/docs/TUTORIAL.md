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

## 10. Add local environment files

Create `.env.example` with the application settings:

```dotenv
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
```

Add `.env`, caches, coverage output, and virtual environments to `.gitignore`.
Add cache and local environment files to `.dockerignore`.

## 11. Add Docker and Compose

Create a `Dockerfile` that:

1. starts from the pinned Python 3.14 image;
2. installs the pinned uv version;
3. installs from `uv.lock`;
4. copies `src/` and `tests/`;
5. switches to a non-root user; and
6. runs the `valkey-flask-demo` project script.

Create `compose.yaml` with three profiles:

- `standalone`: one Valkey node and `app-standalone`;
- `sentinel`: primary, replica, three Sentinel nodes, and `app-sentinel`; and
- `cluster`: three cluster nodes, `cluster-init`, and `app-cluster`.

The full topology definitions are in the final
[`compose.yaml`](../compose.yaml). Publish only Flask on loopback.

Create `infra/sentinel/sentinel.conf` with the `demo-primary` group used by
`VALKEY_SENTINEL_MASTER`.

Checkpoint:

```shell
docker compose --profile standalone config --quiet
docker compose --profile sentinel config --quiet
docker compose --profile cluster config --quiet
```

## 12. Add lifecycle scripts

Create:

- `scripts/common.sh` for the fixed Compose project, topology validation, and
  application service name;
- `scripts/start.sh` to build, wait for Compose health, and wait for
  `/health/ready`;
- `scripts/demo.py` to report the topology and increment the counter twice;
- `scripts/reset.py` to delete only the `demo` counter;
- `scripts/stop.sh` to remove this capsule's resources; and
- `scripts/test-real.sh` to run the same contract against every topology.

Keep the scripts as orchestration. The application behavior stays in Python
modules.

## 13. Add the Make interface

Create a `Makefile` whose stable public targets are:

<!-- markdownlint-disable MD010 -->

```makefile
setup:
	uv sync --frozen

start:
	./scripts/start.sh

reset:
	uv run --frozen python scripts/reset.py

stop:
	./scripts/stop.sh

verify:
	$(MAKE) setup
	$(MAKE) verify-static
	$(MAKE) test-unit
	$(MAKE) test-real
```

<!-- markdownlint-enable MD010 -->

Also add `format`, `lint`, `typecheck`, `test-unit`, and `test-real` targets.
Set `UV_CACHE_DIR` to a capsule-local path so setup remains writable in
restricted environments.

## 14. Add tests in layers

Write tests in this order:

1. `tests/unit/test_config.py` for address parsing and invalid combinations;
2. `tests/unit/test_store.py` for client selection, decoding, Sentinel
   responses, and retry behavior;
3. `tests/unit/test_app.py` using a fake store;
4. `tests/integration/test_store.py` as the shared real-Valkey contract; and
5. `tests/journey/test_http_journey.py` against the running Flask process.

The real test script should start each topology on an available loopback port,
run integration and journey tests, and always clean up through a shell trap.

## 15. Run the finished capsule

Run the standalone journey:

```shell
make setup
make start
make demo
make reset
make stop
```

Repeat it with the other profiles:

```shell
TOPOLOGY=sentinel make start
TOPOLOGY=sentinel make demo
TOPOLOGY=sentinel make stop

TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
TOPOLOGY=cluster make stop
```

Finish the recording with the complete verification:

```shell
make verify
```

The important final message is that the route code stayed unchanged while the
store selected three different connection workflows.

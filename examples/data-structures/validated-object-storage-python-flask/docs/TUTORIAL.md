# Build Validated Pydantic Object Storage

## Recording plan

This tutorial starts with the minimal GLIDE connection pattern and adds typed
objects one layer at a time. The recommended video sequence is:

1. initialize and install;
2. define the two Pydantic models;
3. serialize them through Valkey;
4. expose Flask routes;
5. prove validation failures; and
6. run standalone and cluster.

## CLI presentation

Use bat whenever the recording displays source or configuration:

```shell
bat --paging=never --style=numbers pyproject.toml
bat --paging=never --style=numbers src/validated_objects/models.py
bat --paging=never --style=numbers src/validated_objects/valkey_client.py
bat --paging=never --style=numbers src/validated_objects/app.py
```

Use HTTPie for interactive route calls. Keep curl as an alternative and pipe
its JSON responses through `jq`.

## 1. Initialize the project

```shell
mkdir validated-object-storage-python-flask
cd validated-object-storage-python-flask
uv init \
  --app \
  --package \
  --python 3.14 \
  --name valkey-validated-object-storage-flask \
  --vcs none \
  --build-backend setuptools
```

Create the project layout:

```shell
mkdir -p \
  docs \
  scripts \
  src/validated_objects \
  tests/integration \
  tests/journey \
  tests/unit
touch src/validated_objects/__init__.py
touch src/validated_objects/py.typed
```

Checkpoint: explain that `models.py`, `valkey_client.py`, and `app.py` will be
the complete application.

## 2. Add dependencies

Add the runtime dependencies using their real distribution names:

```shell
uv add \
  Flask==3.1.3 \
  pydantic==2.13.4 \
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

Checkpoint:

```shell
uv run python -c "import flask, pydantic, dotenv, glide_sync"
```

Finish `pyproject.toml` before writing source:

```toml
[build-system]
requires = ["setuptools==80.9.0"]
build-backend = "setuptools.build_meta"

[project]
name = "valkey-validated-object-storage-flask"
version = "0.1.0"
description = "Store validated Pydantic object variants in Valkey strings"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
  "Flask==3.1.3",
  "pydantic==2.13.4",
  "python-dotenv==1.2.3",
  "valkey-glide-sync==2.5.1",
  "waitress==3.0.2",
]

[project.scripts]
validated-object-demo = "validated_objects.app:main"

[dependency-groups]
dev = [
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
validated_objects = ["py.typed"]

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
packages = ["validated_objects"]

[tool.coverage.run]
branch = true
source = ["validated_objects"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

Regenerate the lockfile after the final metadata is in place:

```shell
uv lock
uv sync --frozen
```

## 3. Define reusable constrained types

Create `src/validated_objects/models.py`.

Begin with constrained aliases:

```python
from decimal import Decimal
from typing import Annotated

from pydantic import Field, StringConstraints

ProductName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=80),
]

ProductTag = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[a-z0-9-]+$",
    ),
]

ProductPrice = Annotated[
    Decimal,
    Field(gt=0, max_digits=8, decimal_places=2),
]
```

Explain why `Decimal` is useful for a price and why normalized tags make the
stored representation predictable.

Checkpoint: validate the aliases through the finished model in the next step.

## 4. Create the shared product model

Add imports for `UUID`, `AwareDatetime`, `BaseModel`, and `ConfigDict`, then
define the common fields:

```python
class ProductBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    name: ProductName
    price: ProductPrice
    active: bool
    tags: tuple[ProductTag, ...] = Field(default=(), max_length=5)
    created_at: AwareDatetime
```

Two decisions are visible:

- `extra="forbid"` rejects unknown fields; and
- `frozen=True` prevents accidental mutation after validation.

Checkpoint:

```shell
uv run python -c \
  "from validated_objects.models import ProductBase; print(ProductBase.model_json_schema()['properties'].keys())"
```

## 5. Add physical and digital variants

Add the variant-specific models:

```python
from typing import Literal

from pydantic import HttpUrl


class PhysicalProduct(ProductBase):
    kind: Literal["physical"]
    stock: int = Field(ge=0)
    weight_grams: int = Field(gt=0)


class DigitalProduct(ProductBase):
    kind: Literal["digital"]
    download_url: HttpUrl
    file_size_bytes: int = Field(gt=0)
```

Create the discriminated union and its one reusable adapter:

```python
from pydantic import TypeAdapter

type Product = Annotated[
    PhysicalProduct | DigitalProduct,
    Field(discriminator="kind"),
]

PRODUCT_ADAPTER: TypeAdapter[Product] = TypeAdapter(Product)
```

Checkpoint: validate one object of each type:

```shell
uv run python - <<'PY'
from validated_objects.models import PRODUCT_ADAPTER

product = PRODUCT_ADAPTER.validate_python(
    {
        "kind": "physical",
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Mechanical Keyboard",
        "price": "129.90",
        "active": True,
        "tags": ["hardware"],
        "created_at": "2026-09-03T12:00:00Z",
        "stock": 12,
        "weight_grams": 850,
    }
)
print(type(product).__name__)
print(PRODUCT_ADAPTER.dump_json(product).decode())
PY
```

## 6. Test validation before adding Valkey

Create `tests/unit/test_models.py`.

Cover:

- a valid physical product;
- a valid digital product;
- negative stock;
- zero weight;
- an invalid download URL;
- zero file size;
- an unknown `kind`;
- an unexpected field; and
- a datetime without timezone information.

Checkpoint:

```shell
uv run pytest tests/unit/test_models.py
```

This isolates object-contract problems before persistence is involved.

## 7. Create the topology-aware `ValkeyClient`

Create `src/validated_objects/valkey_client.py`.

Load `.env`, parse the node list, and select the client:

```python
from __future__ import annotations

import os
from uuid import UUID

from dotenv import load_dotenv
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
)

from validated_objects.models import PRODUCT_ADAPTER, Product

load_dotenv()

type GlideClientType = GlideClient | GlideClusterClient


class ValkeyClient:
    key_prefix = "valkey-examples:validated-object:product"

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
```

This capsule trusts `.env`; do not add a settings model here.

Checkpoint: unit-test that each mode calls the corresponding GLIDE factory.

## 8. Add typed persistence methods

Continue the `ValkeyClient` class:

```python
def save(self, product: Product) -> None:
    self.client.set(
        self._key(product.id),
        PRODUCT_ADAPTER.dump_json(product),
    )


def get(self, product_id: UUID) -> Product | None:
    stored = self.client.get(self._key(product_id))
    if stored is None:
        return None
    return PRODUCT_ADAPTER.validate_json(stored)


def delete(self, product_id: UUID) -> bool:
    return self.client.delete([self._key(product_id)]) > 0


def close(self) -> None:
    self.client.close()


def _key(self, product_id: UUID) -> str:
    return f"{self.key_prefix}:{product_id}"
```

Checkpoint: use a fake GLIDE client to prove that `save()` writes JSON bytes
and `get()` returns `PhysicalProduct` or `DigitalProduct`, not a dictionary.

## 9. Build the Flask routes

Create `src/validated_objects/app.py`.

Create the application around one optional client:

```python
def create_app(valkey: ValkeyClient | None = None) -> Flask:
    valkey = valkey or ValkeyClient()
    app = Flask(__name__)
    app.extensions["valkey_client"] = valkey
```

Add the create route:

```python
@app.post("/products")
def create_product() -> tuple[Any, int]:
    product = PRODUCT_ADAPTER.validate_python(request.get_json())
    valkey.save(product)
    body = PRODUCT_ADAPTER.dump_python(product, mode="json")
    return jsonify(body), 201
```

Add read and delete routes:

```python
@app.get("/products/<uuid:product_id>")
def get_product(product_id: UUID) -> tuple[Any, int]:
    product = valkey.get(product_id)
    if product is None:
        return jsonify({"error": "product not found"}), 404
    body = PRODUCT_ADAPTER.dump_python(product, mode="json")
    return jsonify(body), 200


@app.delete("/products/<uuid:product_id>")
def delete_product(product_id: UUID) -> tuple[Any, int]:
    return jsonify({"deleted": valkey.delete(product_id)}), 200
```

Do not add health endpoints; the demo focuses on validation and persistence.

## 10. Return useful validation errors

Register one Pydantic error handler:

```python
@app.errorhandler(ValidationError)
def invalid_product(error: ValidationError) -> tuple[Any, int]:
    errors = json.loads(
        error.json(include_input=False, include_url=False)
    )
    return jsonify({"errors": errors}), 422
```

This removes the original input and documentation URLs while preserving field
locations, error types, and messages.

Add `main()`:

```text
create ValkeyClient
register close() with atexit
create Flask app
serve with Waitress using FLASK_HOST and FLASK_PORT
```

Add the project script:

```toml
[project.scripts]
validated-object-demo = "validated_objects.app:main"
```

Checkpoint:

```shell
uv run pytest tests/unit/test_app.py
```

## 11. Assemble the complete application files

The earlier sections introduced each concept separately. Before adding Docker,
make the three runtime modules complete.

### 11.1 Complete `models.py`

Replace `src/validated_objects/models.py` with:

```python
"""Pydantic models for the product variants stored by the demo."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
)

ProductName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=80),
]
ProductTag = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[a-z0-9-]+$",
    ),
]
ProductPrice = Annotated[
    Decimal,
    Field(gt=0, max_digits=8, decimal_places=2),
]


class ProductBase(BaseModel):
    """Fields shared by every product variant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    name: ProductName
    price: ProductPrice
    active: bool
    tags: tuple[ProductTag, ...] = Field(default=(), max_length=5)
    created_at: AwareDatetime


class PhysicalProduct(ProductBase):
    """A stocked product with a physical shipping weight."""

    kind: Literal["physical"]
    stock: int = Field(ge=0)
    weight_grams: int = Field(gt=0)


class DigitalProduct(ProductBase):
    """A downloadable product with a known file size."""

    kind: Literal["digital"]
    download_url: HttpUrl
    file_size_bytes: int = Field(gt=0)


type Product = Annotated[
    PhysicalProduct | DigitalProduct,
    Field(discriminator="kind"),
]

PRODUCT_ADAPTER: TypeAdapter[Product] = TypeAdapter(Product)
```

### 11.2 Complete `valkey_client.py`

Replace `src/validated_objects/valkey_client.py` with:

```python
"""Connect to Valkey and persist typed Pydantic products."""

from __future__ import annotations

import os
from uuid import UUID

from dotenv import load_dotenv
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
)

from validated_objects.models import PRODUCT_ADAPTER, Product

load_dotenv()

type GlideClientType = GlideClient | GlideClusterClient


class ValkeyClient:
    """Own the GLIDE client plus typed product serialization."""

    key_prefix = "valkey-examples:validated-object:product"

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

    def save(self, product: Product) -> None:
        """Serialize and store one validated product."""

        self.client.set(
            self._key(product.id),
            PRODUCT_ADAPTER.dump_json(product),
        )

    def get(self, product_id: UUID) -> Product | None:
        """Read and reconstruct the correct product variant."""

        stored = self.client.get(self._key(product_id))
        if stored is None:
            return None
        return PRODUCT_ADAPTER.validate_json(stored)

    def delete(self, product_id: UUID) -> bool:
        """Delete one UUID-derived product key."""

        return self.client.delete([self._key(product_id)]) > 0

    def close(self) -> None:
        """Close the underlying GLIDE client."""

        self.client.close()

    def _key(self, product_id: UUID) -> str:
        return f"{self.key_prefix}:{product_id}"
```

### 11.3 Complete `app.py`

Replace `src/validated_objects/app.py` with:

```python
"""Flask routes for validated product storage."""

from __future__ import annotations

import atexit
import json
import os
from typing import Any
from uuid import UUID

from flask import Flask, jsonify, request
from pydantic import ValidationError
from waitress import serve  # type: ignore[import-untyped]

from validated_objects.models import PRODUCT_ADAPTER
from validated_objects.valkey_client import ValkeyClient


def create_app(valkey: ValkeyClient | None = None) -> Flask:
    """Create the Flask application around one typed Valkey client."""

    valkey = valkey or ValkeyClient()
    app = Flask(__name__)
    app.extensions["valkey_client"] = valkey

    @app.get("/")
    def index() -> tuple[Any, int]:
        return jsonify(
            {
                "application": "validated-object-storage",
                "types": ["physical", "digital"],
            }
        ), 200

    @app.post("/products")
    def create_product() -> tuple[Any, int]:
        product = PRODUCT_ADAPTER.validate_python(request.get_json())
        valkey.save(product)
        body = PRODUCT_ADAPTER.dump_python(product, mode="json")
        return jsonify(body), 201

    @app.get("/products/<uuid:product_id>")
    def get_product(product_id: UUID) -> tuple[Any, int]:
        product = valkey.get(product_id)
        if product is None:
            return jsonify({"error": "product not found"}), 404
        body = PRODUCT_ADAPTER.dump_python(product, mode="json")
        return jsonify(body), 200

    @app.delete("/products/<uuid:product_id>")
    def delete_product(product_id: UUID) -> tuple[Any, int]:
        return jsonify({"deleted": valkey.delete(product_id)}), 200

    @app.errorhandler(ValidationError)
    def invalid_product(error: ValidationError) -> tuple[Any, int]:
        errors = json.loads(
            error.json(include_input=False, include_url=False)
        )
        return jsonify({"errors": errors}), 422

    return app


def main() -> None:
    """Create the typed client and run the local WSGI server."""

    valkey = ValkeyClient()
    atexit.register(valkey.close)
    app = create_app(valkey)
    serve(
        app,
        host=os.environ["FLASK_HOST"],
        port=int(os.environ["FLASK_PORT"]),
        threads=4,
    )


if __name__ == "__main__":
    main()
```

Review the completed files:

```shell
bat --paging=never --style=numbers src/validated_objects/models.py
bat --paging=never --style=numbers src/validated_objects/valkey_client.py
bat --paging=never --style=numbers src/validated_objects/app.py
uv run ruff check src
uv run mypy
```

## 12. Add `.env` and project settings

Create `.env.example`:

```dotenv
VALKEY_MODE=standalone
VALKEY_ADDRESSES=standalone-primary:6379,standalone-replica:6379

FLASK_HOST=0.0.0.0
FLASK_PORT=8000
```

Copy it:

```shell
cp .env.example .env
```

Configure Ruff for Python 3.14, strict mypy for `validated_objects`, pytest
markers, branch coverage, and an 85 percent coverage floor in
`pyproject.toml`.

Checkpoint:

```shell
uv run ruff check src tests
uv run mypy
uv run pytest tests/unit --cov
```

## 13. Create the Docker image

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
    && rm -rf /tmp/uv-cache

RUN chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["uv", "run", "--frozen"]
CMD ["validated-object-demo"]
```

The two `uv sync` layers have different purposes:

1. install third-party packages while only lock and project metadata are
   present;
2. copy source and install the local package and console script.

This preserves Docker's dependency cache when only Python source changes. The
container switches to the unprivileged `app` user before startup.

Create `.dockerignore`:

```dockerignore
.cache
.git
.mypy_cache
.pytest_cache
.ruff_cache
.venv
__pycache__
```

Checkpoint:

```shell
bat --paging=never --style=numbers Dockerfile .dockerignore
docker build --tag validated-object-storage:local .
```

## 14. Create the complete Compose topology

Create `compose.yaml`:

```yaml
name: valkey-example-validated-object-storage-python-flask

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

x-cluster-node: &cluster-node
  <<: *valkey
  command:
    - /bin/sh
    - -c
    - >-
      exec valkey-server
      --appendonly no
      --save ""
      --protected-mode no
      --cluster-enabled yes
      --cluster-config-file /data/nodes.conf
      --cluster-node-timeout 5000
      --cluster-announce-hostname "$${HOSTNAME}"
      --cluster-announce-port 6379
      --cluster-announce-bus-port 16379
      --cluster-preferred-endpoint-type hostname
  tmpfs:
    - /data

x-app: &app
  build:
    context: .
    dockerfile: Dockerfile
  image: valkey-example-validated-object-storage-python-flask:local
  restart: "no"
  init: true
  networks:
    - demo
  security_opt:
    - no-new-privileges:true
  env_file:
    - path: .env
      required: false
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
        f"http://127.0.0.1:{os.environ['FLASK_PORT']}/",
        timeout=2)
    interval: 1s
    timeout: 3s
    retries: 60
    start_period: 3s

services:
  standalone-primary:
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

  standalone-replica:
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
      - --replicaof
      - standalone-primary
      - "6379"
    tmpfs:
      - /data
    depends_on:
      standalone-primary:
        condition: service_healthy

  app-standalone:
    <<: *app
    profiles: ["standalone"]
    environment:
      FLASK_HOST: ${FLASK_HOST:-0.0.0.0}
      FLASK_PORT: ${FLASK_PORT:-8000}
      VALKEY_ADDRESSES: standalone-primary:6379,standalone-replica:6379
      VALKEY_MODE: standalone
    depends_on:
      standalone-primary:
        condition: service_healthy
      standalone-replica:
        condition: service_healthy

  cluster-node-1:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-1

  cluster-node-2:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-2

  cluster-node-3:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-3

  cluster-node-4:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-4

  cluster-node-5:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-5

  cluster-node-6:
    <<: *cluster-node
    profiles: ["cluster"]
    hostname: cluster-node-6

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
      - cluster-node-4:6379
      - cluster-node-5:6379
      - cluster-node-6:6379
      - --cluster-replicas
      - "1"
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
      cluster-node-4:
        condition: service_healthy
      cluster-node-5:
        condition: service_healthy
      cluster-node-6:
        condition: service_healthy

  app-cluster:
    <<: *app
    profiles: ["cluster"]
    environment:
      FLASK_HOST: ${FLASK_HOST:-0.0.0.0}
      FLASK_PORT: ${FLASK_PORT:-8000}
      VALKEY_ADDRESSES: cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
      VALKEY_MODE: cluster
    depends_on:
      cluster-init:
        condition: service_completed_successfully

networks:
  demo:
    driver: bridge
```

Read the file in five layers:

1. `x-valkey` defines image, network, security, and health behavior once.
2. `x-cluster-node` adds the cluster flags shared by six nodes.
3. `x-app` builds Flask, publishes only loopback port 8000, and checks `/`.
4. The standalone profile starts a primary, replica, and application.
5. The cluster profile starts six nodes, initializes three shards, and then
   starts the application.

Validate and inspect it:

```shell
docker compose --profile standalone config --quiet
docker compose --profile cluster config --quiet
yq '.services | keys' compose.yaml
bat --paging=never --style=numbers compose.yaml
```

## 15. Add every lifecycle script

### 15.1 Shared topology behavior

Create `scripts/common.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

capsule_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$capsule_root"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$capsule_root/.cache/uv}"
export TOPOLOGY="${TOPOLOGY:-standalone}"
export FLASK_PORT="${FLASK_PORT:-8000}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:${FLASK_PORT}}"

case "$TOPOLOGY" in
  standalone | cluster)
    ;;
  *)
    printf 'TOPOLOGY must be standalone or cluster; received %s\n' \
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
  docker compose --profile standalone --profile cluster "$@"
}
```

### 15.2 Start and wait

Create `scripts/start.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

if ! compose up -d --build --wait "$(app_service)"; then
  printf 'Startup failed for topology %s. Recent application logs:\n' \
    "$TOPOLOGY" >&2
  compose logs --no-color --tail=100 "$(app_service)" >&2 || true
  exit 1
fi

uv run --frozen python scripts/wait_for_http.py \
  "${BASE_URL}/" \
  --timeout 60

printf 'Flask and Valkey are ready: topology=%s url=%s\n' \
  "$TOPOLOGY" "$BASE_URL"
```

Create `scripts/wait_for_http.py`:

```python
"""Wait until an HTTP endpoint returns a successful response."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("--timeout", type=float, default=60)
args = parser.parse_args()

deadline = time.monotonic() + args.timeout
while True:
    try:
        with urllib.request.urlopen(args.url, timeout=2):
            break
    except (OSError, urllib.error.URLError):
        if time.monotonic() >= deadline:
            raise SystemExit(f"Timed out waiting for {args.url}") from None
        time.sleep(0.25)
```

### 15.3 Demonstrate both variants and one failure

Create `scripts/demo.py`:

```python
"""Store two product variants and show one validation failure."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

PHYSICAL_ID = "11111111-1111-4111-8111-111111111111"
DIGITAL_ID = "22222222-2222-4222-8222-222222222222"

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")


def send(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


physical = {
    "kind": "physical",
    "id": PHYSICAL_ID,
    "name": "Mechanical Keyboard",
    "price": "129.90",
    "active": True,
    "tags": ["hardware", "keyboard"],
    "created_at": "2026-09-03T12:00:00Z",
    "stock": 12,
    "weight_grams": 850,
}
digital = {
    "kind": "digital",
    "id": DIGITAL_ID,
    "name": "Valkey Demo Guide",
    "price": "19.99",
    "active": True,
    "tags": ["guide", "valkey"],
    "created_at": "2026-09-03T12:00:00Z",
    "download_url": "https://example.com/downloads/valkey-guide.pdf",
    "file_size_bytes": 5_242_880,
}
invalid = {
    **physical,
    "id": "33333333-3333-4333-8333-333333333333",
    "stock": -1,
}

for label, payload in (("physical", physical), ("digital", digital)):
    status, _ = send("POST", "/products", payload)
    print(f"{label} POST -> {status}")
    status, body = send("GET", f"/products/{payload['id']}")
    print(f"{label} GET  -> {status} {body['kind']} product")

status, body = send("POST", "/products", invalid)
print(f"invalid POST  -> {status} {body['errors'][0]['msg']}")
```

Create `scripts/reset.py`:

```python
"""Delete the two deterministic demo products."""

from __future__ import annotations

import json
import os
import urllib.request

DEMO_IDS = (
    "11111111-1111-4111-8111-111111111111",
    "22222222-2222-4222-8222-222222222222",
)

port = os.environ.get("FLASK_PORT", "8000")
base_url = os.environ.get("BASE_URL", f"http://127.0.0.1:{port}")

for product_id in DEMO_IDS:
    request = urllib.request.Request(
        f"{base_url}/products/{product_id}",
        method="DELETE",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        print(json.load(response))
```

### 15.4 Stop all owned resources

Create `scripts/stop.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

compose_all down --remove-orphans --volumes
printf 'Stopped resources owned by validated-object-storage-python-flask.\n'
```

### 15.5 Test both real topologies

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
  test_port="$(
    uv run --frozen python -c \
      'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'
  )"
  base_url="http://127.0.0.1:${test_port}"

  printf '\n== Verify %s topology ==\n' "$topology"
  cleanup

  TOPOLOGY="$topology" FLASK_PORT="$test_port" ./scripts/start.sh

  TOPOLOGY="$topology" FLASK_PORT="$test_port" \
    docker compose --profile "$topology" run \
    --rm \
    --no-deps \
    "app-$topology" \
    pytest tests/integration

  BASE_URL="$base_url" EXPECTED_TOPOLOGY="$topology" \
    uv run --frozen pytest tests/journey

  TOPOLOGY="$topology" FLASK_PORT="$test_port" ./scripts/stop.sh
done
```

Make the shell scripts executable:

```shell
chmod +x scripts/common.sh scripts/start.sh scripts/stop.sh scripts/test-real.sh
```

## 16. Add the Make interface and tests

Create `Makefile`:

<!-- markdownlint-disable MD010 -->

```makefile
SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start stop reset demo format lint typecheck test-unit \
	test-real verify-static verify

help:
	@printf '%s\n' \
		"setup        Install the locked Python environment" \
		"start        Start TOPOLOGY=standalone|cluster (default: standalone)" \
		"stop         Stop this capsule's Compose resources" \
		"reset        Delete the two known demo products" \
		"demo         Store typed products and show a validation failure" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run integration and HTTP journeys against both topologies" \
		"verify       Run every static and behavioral check"

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
```

<!-- markdownlint-enable MD010 -->

Create tests in this order:

1. `tests/unit/test_models.py` for both variants and validation failures;
2. `tests/unit/test_valkey_client.py` for JSON round trips and client choice;
3. `tests/unit/test_app.py` for HTTP 201, 404, and 422 behavior;
4. `tests/integration/test_client.py` for real standalone and cluster storage;
5. `tests/journey/test_http.py` for the running application journey.

The complete test files are in the final capsule. They use deterministic UUIDs
and delete only those product keys.

## 17. Run the finished capsule

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
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

Complete verification:

```shell
make verify
```

End the recording by showing the complete round trip:

```text
request JSON
-> Pydantic Product
-> JSON bytes in Valkey
-> Pydantic Product
-> response JSON
```

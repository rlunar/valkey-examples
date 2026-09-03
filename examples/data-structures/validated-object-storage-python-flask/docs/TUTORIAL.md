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

## 11. Add `.env` and project settings

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

## 12. Add Docker and the standalone pair

Create a non-root `Dockerfile` that installs the locked uv environment and
runs `validated-object-demo`.

In `compose.yaml`, add:

- `standalone-primary`;
- `standalone-replica`;
- `app-standalone`; and
- a private `demo` network.

Provide these application variables:

```yaml
VALKEY_MODE: standalone
VALKEY_ADDRESSES: standalone-primary:6379,standalone-replica:6379
```

Publish only the Flask port on loopback.

Checkpoint:

```shell
docker compose --profile standalone config --quiet
```

## 13. Add the three-shard cluster

Add six cluster-enabled nodes and a `cluster-init` service that creates three
primaries with one replica each.

Configure `app-cluster` with:

```yaml
VALKEY_MODE: cluster
VALKEY_ADDRESSES: cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
```

Use the final [`compose.yaml`](../compose.yaml) as the complete reference for
pinned images, node hostnames, health checks, and dependencies.

Checkpoint:

```shell
docker compose --profile cluster config --quiet
```

## 14. Add the visible demo script

Create `scripts/demo.py` with:

- one deterministic physical product;
- one deterministic digital product; and
- one invalid physical product whose stock is `-1`.

For each valid payload, send `POST /products` and then
`GET /products/<uuid>`. Print the returned `kind`. For the invalid payload,
print the 422 status and first validation message.

Create `scripts/reset.py` to delete only the two deterministic valid UUIDs.

Checkpoint: the expected output should read:

```text
physical POST -> 201
physical GET  -> 200 physical product
digital POST -> 201
digital GET  -> 200 digital product
invalid POST  -> 422 Input should be greater than or equal to 0
```

## 15. Add lifecycle and real tests

Add shell scripts for start, stop, and real verification. Add a `Makefile`
exposing:

```text
make setup
make start
make demo
make reset
make verify
make stop
```

Create `tests/integration/test_client.py` to round-trip both variants through
real Valkey.

Create `tests/journey/test_http.py` to verify:

- HTTP 201 for valid objects;
- the correct `kind` on GET;
- HTTP 422 for invalid constraints;
- HTTP 404 for missing products; and
- deletion of only the requested UUID.

Run the same tests against standalone and cluster.

## 16. Run the finished capsule

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

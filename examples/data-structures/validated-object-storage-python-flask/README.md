# Validated Object Storage with Pydantic

This capsule extends the
[Valkey GLIDE Flask quickstart](../../operations/client-quickstart-python-flask/)
with typed object validation and serialization. It stores physical and digital
products as JSON in ordinary Valkey strings and reconstructs the correct
Pydantic type when they are read.

## What you will see

The model demonstrates:

- UUID, string, decimal, boolean, tuple, and timezone-aware datetime fields;
- constrained names, prices, tags, stock, weight, URLs, and file sizes;
- a discriminated union selected by `kind`;
- rejection of unexpected fields; and
- JSON round trips through standalone Valkey or Valkey Cluster.

The domain vocabulary is recorded in [CONTEXT.md](CONTEXT.md).

## Documentation

- [Design, architecture, and pseudocode](docs/DESIGN.md)
- [Step-by-step demo runbook](docs/DEMO.md)
- [Build-from-scratch video tutorial](docs/TUTORIAL.md)

## Architecture

The Flask process validates each request as one of the two product variants.
`ValkeyClient` then serializes that typed object and connects to exactly one
topology selected by `VALKEY_MODE`.

```mermaid
flowchart LR
    caller["Demo caller<br/>make demo"]

    subgraph application["Flask application"]
        flask["HTTP routes<br/>app.py"]
        model["Pydantic Product<br/>PhysicalProduct | DigitalProduct"]
        client["ValkeyClient<br/>save | get | delete"]

        flask -->|"validate request"| model
        flask -->|"typed Product"| client
        client -->|"dump_json / validate_json"| model
    end

    topology["Topology selection<br/>VALKEY_MODE"]

    subgraph deployment["Selected Valkey deployment"]
        standalone["Standalone<br/>1 primary + 1 replica"]
        cluster["Cluster<br/>3 primaries + 3 replicas"]
    end

    caller -->|"POST / GET / DELETE"| flask
    client -->|"GLIDE connection"| topology
    topology -->|"standalone"| standalone
    topology -->|"cluster"| cluster
```

Only one deployment branch runs at a time. On writes, validation happens before
`SET`; on reads, stored JSON is validated again to reconstruct the correct
physical or digital product type.

## Quick walkthrough

Prerequisites are Docker with Compose, Python 3.14, uv, Make, ShellCheck,
HTTPie, jq, and bat.

```shell
cp .env.example .env
make setup
make start
make demo
make stop
```

The demonstration stores and retrieves one physical product and one digital
product, then sends an invalid physical product:

```text
physical POST -> 201
physical GET  -> physical product
digital POST  -> 201
digital GET   -> digital product
invalid POST  -> 422
```

Run the same application against the six-node cluster:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
make stop
```

## The important code

[`models.py`](src/validated_objects/models.py) defines the two product variants
and their validation rules. [`valkey_client.py`](src/validated_objects/valkey_client.py)
uses one Pydantic `TypeAdapter` to serialize and reconstruct the union:

```python
self.client.set(self._key(product.id), PRODUCT_ADAPTER.dump_json(product))
return PRODUCT_ADAPTER.validate_json(stored)
```

[`app.py`](src/validated_objects/app.py) validates requests before calling the
client:

```python
product = PRODUCT_ADAPTER.validate_python(request.get_json())
valkey.save(product)
```

Validation errors become HTTP 422 responses. Missing products return HTTP 404.

## Validation flow

```mermaid
sequenceDiagram
    participant caller as Demo caller
    participant flask as Flask
    participant model as Pydantic Product
    participant valkey as Valkey

    caller->>flask: POST /products
    flask->>model: validate input
    alt product is valid
        model-->>flask: PhysicalProduct or DigitalProduct
        flask->>valkey: SET UUID key, JSON value
        valkey-->>flask: OK
        flask-->>caller: 201 typed product
    else validation fails
        model-->>flask: ValidationError
        flask-->>caller: 422 field errors
    end
```

## Data representation

Each product uses one key:

```text
valkey-examples:validated-object:product:<uuid>
```

The value is Pydantic-generated JSON. Decimal prices are represented without
binary floating-point loss, datetimes retain their timezone, and the `kind`
field selects the object variant during reconstruction.

## Lifecycle and verification

```shell
make reset
make verify
make stop
```

`make reset` removes only the two deterministic demo UUIDs. `make verify` runs
Ruff, ShellCheck, strict mypy, unit tests, and real integration and HTTP
journeys against both topologies.

## Versions and resources

- Python 3.14.7
- Flask 3.1.3
- Pydantic 2.13.4
- valkey-glide-sync 2.5.1
- Valkey 9.1.1

Allow up to 4 CPU cores, 2 GB of memory, 3 GB of disk, 1.5 GB of initial
downloads, and 15 minutes for the first full verification.

## Security and production limitations

Flask binds to loopback. Valkey stays on the private Compose network but uses
no authentication or TLS. This demonstration has no schema migration,
secondary indexes, concurrency controls, or compatibility policy for old
objects. It is not an object-mapping framework or production deployment
reference.

The default journey requires no credentials and uses no third-party data.
Repository-authored content is MIT licensed; dependencies and images retain
their own licenses.

This capsule is a candidate owned by `rlunar`, with `valkey-io` as backup.
Repository admission remains blocked until the maintainers, reviewers, and
runtime CI described in the repository root are established.

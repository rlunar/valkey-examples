# Validated Object Storage Demo Runbook

## Demo goal

Show three outcomes:

1. a physical product validates and round-trips through Valkey;
2. a digital product reconstructs as a different Pydantic type; and
3. an invalid product receives HTTP 422 before any `SET`.

## Prepare once

From the capsule root:

```shell
http --version
jq --version
bat --version
cp .env.example .env
make setup
```

The default demo uses the standalone primary and replica and publishes Flask
at `http://127.0.0.1:8000`. HTTPie, jq, and bat are used for the
presenter-facing commands.

## Part 1: show the object contract

Display [`src/validated_objects/models.py`](../src/validated_objects/models.py)
with syntax highlighting:

```shell
bat --paging=never --style=numbers src/validated_objects/models.py
```

Highlight:

```python
type Product = Annotated[
    PhysicalProduct | DigitalProduct,
    Field(discriminator="kind"),
]
```

Then show one validation difference:

```python
class PhysicalProduct(ProductBase):
    stock: int = Field(ge=0)
    weight_grams: int = Field(gt=0)


class DigitalProduct(ProductBase):
    download_url: HttpUrl
    file_size_bytes: int = Field(gt=0)
```

Suggested narration:

> `kind` selects the model. Physical and digital products share core fields,
> but each type has fields that are required and validated for that type.

## Part 2: show serialization

Display
[`src/validated_objects/valkey_client.py`](../src/validated_objects/valkey_client.py):

```shell
bat --paging=never --style=numbers src/validated_objects/valkey_client.py
```

Highlight:

```python
self.client.set(self._key(product.id), PRODUCT_ADAPTER.dump_json(product))
return PRODUCT_ADAPTER.validate_json(stored)
```

Suggested narration:

> The object becomes JSON on write and becomes the correct Pydantic type again
> on read. Valkey stores an ordinary string value.

## Part 3: run standalone

Start the application and standalone pair:

```shell
make start
```

Run the prepared journey:

```shell
make demo
```

Expected output:

```text
physical POST -> 201
physical GET  -> 200 physical product
digital POST -> 201
digital GET  -> 200 digital product
invalid POST  -> 422 Input should be greater than or equal to 0
```

Explain that the invalid payload changes physical stock to `-1`. Pydantic
rejects it before `ValkeyClient.save()` runs.

Clean up the two deterministic demo products:

```shell
make reset
make stop
```

## Part 4: inspect one object manually

Start the standalone demo:

```shell
make start
```

Create a physical product:

```shell
http --ignore-stdin POST :8000/products \
  kind=physical \
  id=11111111-1111-4111-8111-111111111111 \
  name="Mechanical Keyboard" \
  price=129.90 \
  active:=true \
  tags:='["hardware", "keyboard"]' \
  created_at=2026-09-03T12:00:00Z \
  stock:=12 \
  weight_grams:=850
```

Read it:

```shell
http --ignore-stdin GET \
  :8000/products/11111111-1111-4111-8111-111111111111
```

Submit an invalid physical product:

```shell
http --ignore-stdin --print=Hhb POST :8000/products \
  kind=physical \
  id=33333333-3333-4333-8333-333333333333 \
  name="Broken Product" \
  price=10.00 \
  active:=true \
  tags:='[]' \
  created_at=2026-09-03T12:00:00Z \
  stock:=-1 \
  weight_grams:=100
```

The response status is HTTP 422 and identifies the `stock` constraint.

The equivalent curl request should format the JSON body with `jq`:

```shell
curl -sS \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "physical",
    "id": "11111111-1111-4111-8111-111111111111",
    "name": "Mechanical Keyboard",
    "price": "129.90",
    "active": true,
    "tags": ["hardware", "keyboard"],
    "created_at": "2026-09-03T12:00:00Z",
    "stock": 12,
    "weight_grams": 850
  }' \
  http://127.0.0.1:8000/products |
  jq
```

Finish with:

```shell
make reset
make stop
```

## Part 5: run the cluster variation

Start three shards with one replica each:

```shell
TOPOLOGY=cluster make start
```

Run the same object journey:

```shell
TOPOLOGY=cluster make demo
```

The output is the same because the object model and key representation are
independent of the selected GLIDE client.

Stop the cluster:

```shell
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

## Full verification

Before publishing a recording:

```shell
make verify
```

This runs static checks, model and route unit tests, and real object
round-trips against standalone and cluster.

## Recovery

If port 8000 is occupied:

```shell
FLASK_PORT=8010 make start
FLASK_PORT=8010 make demo
FLASK_PORT=8010 make stop
```

If startup fails:

```shell
docker compose --profile standalone logs --tail=100 app-standalone
docker compose --profile cluster logs --tail=100 app-cluster
```

Remove only this capsule's resources:

```shell
docker compose \
  --profile standalone \
  --profile cluster \
  down --remove-orphans --volumes
```

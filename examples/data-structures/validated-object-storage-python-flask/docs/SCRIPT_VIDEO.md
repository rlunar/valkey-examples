# Validated Object Storage Tutorial Video Script

## Production contract

- Format: narrated terminal tutorial
- Target duration: 7–8 minutes
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)

The replicated standalone journey completes before five minutes. Cluster is an
optional variation afterward.

## Prepare off camera

```shell
cp -n .env.example .env
make setup
make verify
make stop
```

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:25 | Preview the physical, digital, and invalid outcomes | “You will validate two product shapes, persist them as JSON in Valkey, reconstruct their types, and reject invalid stock.” | Finished result |
| 00:25–01:05 | Render the architecture | “Flask receives JSON, Pydantic selects and validates a product type, and `ValkeyClient` persists the validated representation.” | Architecture |
| 01:05–02:00 | Show constrained shared fields | “Reusable constraints protect names, prices, tags, identifiers, and timestamps before storage.” | Domain model |
| 02:00–02:50 | Show physical and digital variants | “A discriminator named `kind` selects fields such as stock and weight or download URL and file size.” | Typed variants |
| 02:50–03:30 | Show `save()` and `get()` | “Writes use Pydantic JSON serialization. Reads validate the stored JSON again and rebuild the correct class.” | Persistence adapter |
| 03:30–04:05 | Run `make start` | “The cached Flask and replicated standalone profile become ready.” | Readiness |
| 04:05–04:45 | Run `make demo` | “Two valid products round-trip. The invalid request returns 422 without calling SET.” | Behavioral proof |
| 04:45–05:00 | Reset and stop | “The primary build is complete and both deterministic keys are removed.” | Five-minute checkpoint |
| 05:00–06:30 | Optional: inspect stored JSON and validation flow | “Valkey remains schema-agnostic; the application owns type validation.” | Deeper explanation |
| 06:30–07:30 | Optional: repeat against cluster | “The storage contract stays identical while GLIDE changes the connection type.” | Topology variation |

## Exact recording commands

```shell
sed -n '/^## Architecture$/,/^## Domain model$/p' \
  docs/DESIGN.md |
  glow - --width 90

bat --paging=never --style=numbers \
  --highlight-line 39:72 \
  src/validated_objects/models.py
bat --paging=never --style=numbers \
  --highlight-line 33:57 \
  src/validated_objects/valkey_client.py

make start
make demo
make reset
make stop
```

Optional cluster chapter:

```shell
TOPOLOGY=cluster make start
TOPOLOGY=cluster make demo
TOPOLOGY=cluster make reset
TOPOLOGY=cluster make stop
```

## Verification

- [ ] The standalone journey succeeds before 05:00.
- [ ] The video distinguishes validation from serialization.
- [ ] Cluster begins only after the primary checkpoint.
- [ ] Cleanup removes both deterministic product keys.

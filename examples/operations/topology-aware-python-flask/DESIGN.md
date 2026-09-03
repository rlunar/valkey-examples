# Design Notes

## Goal

This capsule is a foundation for demos, not an application framework. Its
design optimizes for a reader who needs to copy the directory, replace the
counter behavior, and retain configuration, lifecycle, topology selection,
observability, and tests.

## Deep modules

The implementation has two behavior-rich classes.

### `ValkeyStore`

Its interface contains only operations the Flask application needs:

```python
get(name)
increment(name)
delete(name)
ping()
topology_snapshot()
close()
```

The implementation hides:

- `GlideClient` versus `GlideClusterClient`;
- GLIDE configuration objects;
- standalone role discovery;
- Sentinel commands and response decoding;
- Sentinel primary replacement and one retry;
- bytes-to-integer conversion;
- key construction; and
- safe topology metadata.

Deleting this module would push topology branching and GLIDE result handling
into every route and test, so the module earns its interface.

### `FlaskDemo`

This class keeps route registration, request IDs, JSON responses, error
translation, and request completion logs local. It accepts the `CounterStore`
interface, making the same seam available to application callers and unit
tests.

The Flask application factory is the public construction interface:

```python
create_app(settings=None, store=None)
```

Future demos can keep that interface while replacing the counter routes and
store methods.

## Why there are no topology subclasses

Standalone, Sentinel, and cluster share nearly all counter behavior. Three
public store subclasses would expose construction details without giving
callers more leverage. The variation stays private inside `ValkeyStore`.

If future requirements produce materially different command behavior, a second
real adapter can be introduced at the existing `CounterStore` seam.

## Sentinel support

Valkey GLIDE 2.5.1 has standalone and cluster clients but no Sentinel client.
The implementation therefore uses GLIDE for both steps:

1. create a short-lived standalone client with `NodeDiscoveryMode.STATIC` so it
   does not classify a Sentinel node as a data primary;
2. send `SENTINEL GET-MASTER-ADDR-BY-NAME`;
3. validate the two-field host and port response;
4. close the discovery client; and
5. create the process-lifetime standalone data client for that primary.

Sentinel-backed commands are serialized through a process-local lock. If GLIDE
raises an error, the store discovers the primary again, replaces the data
client, and retries once. This is deliberately bounded and visible.

## Cluster-safe keys

Each counter operation uses one key:

```text
valkey-examples:flask-base:v1:counter:<validated-name>
```

No operation spans keys, so cluster hash-tag coordination is unnecessary. The
reset path deletes exactly `counter:demo`; tests use UUIDv7-scoped names and
delete them in cleanup.

## Configuration

`AppSettings` is immutable. It parses comma-separated bootstrap addresses,
including bracketed IPv6, and rejects:

- missing or invalid ports;
- more than 32 bootstrap addresses;
- a nonzero cluster database;
- unsafe key-prefix characters; and
- non-HTTP OTLP endpoints.

Validation happens before `ValkeyStore` opens a connection.

## Observability

The application always emits structured JSON logs. When OpenTelemetry is
enabled:

- logging instrumentation injects trace and span identifiers;
- Flask instrumentation creates server spans;
- a configured OTLP endpoint receives batched application spans and logs; and
- GLIDE exports its own traces to the same endpoint.

The OTLP backend is optional so the credential-free local journey remains
self-contained.

## Runtime ownership

One process-lifetime store is created by the application factory. `main()`
registers `close()` with `atexit` and serves the Flask app through Waitress.
Flask request teardown does not close the store because teardown runs after
every request.

Compose owns the application and Valkey processes. The application container is
the only service with a published port.

## Extension guide

For a new Flask demo:

1. keep `AppSettings`, telemetry, lifecycle scripts, and Compose app settings;
2. replace `CounterSnapshot` with the demo's response models;
3. replace the counter methods on the store interface with a small
   capability-oriented interface;
4. keep topology selection private to the Valkey implementation; and
5. update the shared real-Valkey contract so every supported topology proves
   the new behavior.

Avoid adding a class for each route, command, response, or topology unless a
second implementation creates a real seam.

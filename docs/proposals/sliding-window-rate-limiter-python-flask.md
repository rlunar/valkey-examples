---
proposal: Sliding-window rate limiter with Python, Flask, GLIDE, and Valkey
status: Draft
date: 2026-08-24
kind: Demo
capability: Rate limiter
proposed_path: examples/rate-limiter/sliding-window-python-flask
---

# Design Proposal: Sliding-Window Rate Limiter

## Decision requested

Approve a focused Python demo that uses Flask, Valkey GLIDE, and a Valkey sorted
set to enforce an atomic sliding-window request limit.

Approval authorizes implementation planning only. The capsule must remain in
`candidate` status until owners, reviewers, exact dependency versions, the
Valkey image digest, runtime CI, security scanning, and clean-clone
reproduction are complete.

## Summary

The proposed demo exposes one rate-limited HTTP endpoint. A caller supplies a
demonstration client identifier, sends requests, and observes:

1. requests within the configured limit return HTTP 200;
2. response metadata shows the limit, remaining capacity, and reset time;
3. the first request above the limit returns HTTP 429;
4. the response includes a bounded retry time; and
5. the caller is admitted again after the oldest request leaves the rolling
   window.

Valkey stores one sorted set per policy and client identity. Each accepted
request is a unique member scored with Valkey server time in milliseconds. One
server-side Lua script removes expired members, counts the active window,
conditionally records the request, refreshes expiration, and returns the rate
limit decision atomically.

## Why this belongs in Valkey Examples

The proposal passes the repository placement test:

- its primary purpose is to make Valkey sorted-set behavior observable;
- it is a focused demo with one learning objective;
- the default path uses released public dependencies;
- Valkey runs locally without credentials;
- CI can execute the complete journey against real Valkey;
- the capsule can be independently tested, copied, deprecated, or removed; and
- it requires no independent release or security-advisory lifecycle.

The proposed capability is `rate-limiter` because rate limiting is the
developer's primary learning goal. Sorted sets, scores, cardinality, range
removal, and expiration are the Valkey mechanisms taught by the implementation.

## Goals

The demo must:

- teach a true sliding-window log algorithm rather than a fixed-window counter;
- use a Valkey sorted set as the source of truth;
- make the concurrency guarantee explicit and test it;
- use Valkey server time to avoid application-host clock skew;
- use Python 3.13 or newer, with Python 3.13 as the initial tested baseline;
- use uv for Python acquisition, locking, installation, and command execution;
- use Flask as a small HTTP adapter;
- use the synchronous Valkey GLIDE Python client;
- run Valkey from `valkey/valkey:9-alpine` with an immutable digest;
- remain credential-free and runnable from a clean clone;
- reach the first visible rate-limit decision within five minutes; and
- expose all behavior through the capsule's standard `make` interface.

## Non-goals

The first version will not:

- provide production authentication or authorization;
- trust `X-Forwarded-For` or configure a reverse proxy;
- implement distributed policy administration;
- provide per-route configuration through a database or user interface;
- compare rate-limiting algorithms or publish performance claims;
- use Valkey Cluster, Sentinel, replicas, TLS, or ACLs;
- package a reusable Flask extension or Python library;
- run the Flask application in an Alpine container; or
- claim that the example is a production-certified rate limiter.

## Proposed capsule

```text
examples/rate-limiter/sliding-window-python-flask/
├── example.yaml
├── README.md
├── DESIGN.md
├── Makefile
├── compose.yaml
├── .env.example
├── .python-version
├── pyproject.toml
├── uv.lock
├── src/
│   └── rate_limiter_demo/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── decision.py
│       ├── identity.py
│       ├── limiter.py
│       ├── valkey_limiter.py
│       └── scripts/
│           └── sliding_window.lua
└── tests/
    ├── unit/
    ├── integration/
    └── journey/
```

The proposal document will become the capsule's `DESIGN.md` when implementation
is approved.

Directories will be added only when they contain required files. No shared
repository runtime package will be introduced.

## Runtime topology

```text
HTTP client
    |
    v
Flask HTTP adapter
    |
    v
RateLimiter interface
    |
    v
ValkeySlidingWindow adapter
    |
    v
GLIDE sync client + cached Script
    |
    v
valkey/valkey:9-alpine
```

Only Valkey runs in Docker in the default journey. The Flask process runs on
the host through uv.

This separation is intentional: the checked-out GLIDE Python project supports
Python 3.13 and provides a synchronous package, but explicitly does not support
Alpine Linux or other musl-based Python environments. A future containerized
Flask adapter would therefore use a compatible glibc-based Python image, not
Alpine.

## Module design

### Flask HTTP adapter

The Flask module owns:

- request parsing and input validation;
- mapping a decision to JSON, response headers, and HTTP status;
- liveness and readiness endpoints; and
- mapping dependency failures to HTTP 503.

It does not know sorted-set commands, Lua return positions, key formats, or
GLIDE result encodings.

The application will use a Flask application factory. The rate limiter is
accepted as a dependency rather than created inside route handlers.

### RateLimiter interface

The external seam is one operation:

`check(identity, policy, request_id) -> decision`

The interface includes these invariants:

- one call represents one attempted request;
- the returned decision contains `allowed`, `limit`, `remaining`,
  `reset_after_ms`, and `retry_after_ms`;
- `remaining` is never negative;
- `retry_after_ms` is zero for an allowed request;
- a dependency failure is an error, not a deny decision; and
- callers do not depend on Valkey, GLIDE, Lua, or sorted-set result types.

The small interface gives the HTTP adapter one test surface while keeping
atomicity, key construction, script invocation, and result decoding local to
the Valkey implementation.

### ValkeySlidingWindow adapter

The Valkey adapter owns:

- deriving a bounded, non-sensitive key;
- constructing and retaining the GLIDE `Script` object;
- invoking the script with exactly one key;
- validating and decoding the script result;
- translating GLIDE failures into a dependency error; and
- closing the GLIDE client during application shutdown.

The GLIDE client is created once per Flask process, not once per request.
Application teardown must not close the shared client after every request.
Multi-process servers must create clients after worker processes are forked.

### Identity adapter

The demo endpoint requires an `X-Client-ID` header so the scripted journey can
select identities deterministically.

The raw identifier:

- is limited to a documented maximum length;
- is never embedded directly in a Valkey key;
- is hashed before storage;
- is never written to logs; and
- is explicitly described as demonstration input, not authentication.

The default design does not trust proxy headers. A production application
would normally derive identity from an authenticated subject or an explicitly
trusted proxy configuration.

## Sliding-window algorithm

### Key

Each policy and identity uses one key:

`valkey-examples:rate-limit:v1:<policy-id>:<identity-hash>`

Only one key is passed to the script, so the algorithm remains cluster-slot
safe if cluster support is added later.

### Sorted-set representation

- The score is Valkey server time in Unix milliseconds.
- The member is the timestamp plus an application-generated unique request ID.
- Multiple requests in the same millisecond remain distinct members.
- The sorted-set cardinality is bounded by the configured request limit because
  denied requests are not inserted.

Unix time in milliseconds remains within the exactly representable integer
range documented for sorted-set scores.

### Atomic decision

For one attempted request, the script:

1. validates the limit and window arguments;
2. obtains the current time from Valkey with `TIME`;
3. computes the inclusive expiration cutoff;
4. removes scores at or before the cutoff with `ZREMRANGEBYSCORE`;
5. reads the active count with `ZCARD`;
6. allows the request only when the count is below the configured limit;
7. for an allowed request, adds one unique member with `ZADD`;
8. refreshes the key expiration with `PEXPIRE`;
9. reads the oldest active score needed to calculate reset time; and
10. returns a fixed-position array containing the decision and timing values.

The script is the atomicity seam. The design rejects a sequence of independent
client commands because concurrent Flask workers could otherwise admit more
requests than the policy permits.

An entry whose timestamp is exactly one full window old is expired. This rule
must be stated in tests so boundary behavior is not implementation-dependent.

### Script execution

The synchronous GLIDE `Script` interface is used because it:

- retains script code and its hash;
- automatically uses cached script execution;
- accepts explicit key and argument arrays;
- routes a keyed invocation correctly; and
- avoids wrapping the operation in a second transaction layer.

The script object is created once and retained for the process lifetime.

## HTTP interface

### `GET /api/limited`

Required request header:

`X-Client-ID: <demonstration identity>`

Allowed response:

- status: `200 OK`;
- JSON fields: `allowed`, `limit`, `remaining`, `reset_after_ms`; and
- headers: `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset`.

Denied response:

- status: `429 Too Many Requests`;
- JSON fields: `allowed`, `limit`, `remaining`, `reset_after_ms`, and
  `retry_after_ms`; and
- headers: the rate-limit fields plus `Retry-After`.

`Retry-After` is rounded up to whole seconds. JSON retains millisecond precision
so the behavior is easy to inspect.

Missing or invalid identity input returns HTTP 400 and does not call Valkey.

### `GET /health/live`

Returns HTTP 200 when the Flask process is running. It does not query Valkey.

### `GET /health/ready`

Returns HTTP 200 only when the GLIDE client can reach Valkey. Dependency
failures return HTTP 503.

## Configuration

The default demonstration policy is proposed as five requests per ten-second
sliding window.

Configuration will be provided through environment variables:

| Setting | Default | Constraint |
| --- | --- | --- |
| `VALKEY_HOST` | `127.0.0.1` | Non-empty hostname |
| `VALKEY_PORT` | `6379` | Valid TCP port |
| `GLIDE_REQUEST_TIMEOUT_MS` | `500` | Positive and bounded |
| `RATE_LIMIT_REQUESTS` | `5` | Positive and bounded |
| `RATE_LIMIT_WINDOW_MS` | `10000` | Positive and bounded |
| `RATE_LIMIT_POLICY_ID` | `demo` | Lower-case bounded slug |
| `RATE_LIMIT_KEY_PREFIX` | `valkey-examples:rate-limit:v1` | Fixed by default |
| `FLASK_HOST` | `127.0.0.1` | Loopback default |
| `FLASK_PORT` | `8000` | Valid TCP port |

Invalid configuration fails application startup rather than falling back to an
unknown policy.

## Dependency and runtime choices

### Python and uv

- `requires-python` declares Python 3.13 as the minimum.
- `.python-version` records the exact tested Python 3.13 patch selected during
  implementation.
- `uv.lock` is committed.
- setup uses `uv sync --frozen`.
- all Python commands run through `uv run`.

Python versions newer than 3.13 are not added to the tested compatibility
matrix until the selected GLIDE release publishes compatible wheels and CI
passes.

### Flask

Flask is the synchronous HTTP adapter. Its exact released version is selected
and locked during implementation.

The built-in development server is used only for the local educational journey.
The README will explicitly state that it is not a production server.

### Valkey GLIDE

The capsule uses the `valkey-glide-sync` distribution and the `glide_sync`
import namespace.

The exact released version is selected and locked during implementation.
Direct sorted-set calls may be used for test inspection, but the runtime
decision uses the cached `Script` interface so the complete algorithm executes
atomically.

### Valkey container

The Compose service uses the requested `valkey/valkey:9-alpine` image and records
the resolved immutable digest:

`valkey/valkey:9-alpine@sha256:<resolved-digest>`

This preserves the requested major Alpine tag while satisfying the repository's
immutable-image requirement.

The service:

- binds port 6379 to loopback only;
- declares a `valkey-cli ping` health check;
- uses ephemeral data for deterministic reset and cleanup;
- requires no credentials on the local path; and
- documents that no authentication and no TLS are unsafe outside local
  development.

## Failure behavior

If Valkey is unavailable, the script fails, or the GLIDE result cannot be
validated, the endpoint returns HTTP 503.

The demo does not silently fail open and does not misreport a dependency
failure as HTTP 429. This makes the learning outcome and operational limitation
visible.

Logs include the decision, policy ID, HTTP status, and latency. They do not
include the raw client identity, full derived key, or script arguments.

## Test strategy

### Unit tests

Unit tests cover:

- configuration validation;
- identity normalization, bounds, and hashing;
- key construction;
- script-result decoding and invariant checks;
- HTTP response and header mapping;
- missing and invalid identity behavior; and
- dependency-error mapping to HTTP 503.

The HTTP adapter uses a fake `RateLimiter` implementation. Tests do not reach
past the interface to assert GLIDE internals.

### Integration tests

Integration tests run against the requested real Valkey container and verify:

- requests up to the limit are allowed;
- the next request is denied;
- exactly the configured number of concurrent requests are allowed;
- denied requests do not increase sorted-set cardinality;
- entries at the window cutoff are removed;
- same-millisecond requests remain distinct;
- reset and retry times are positive and bounded;
- key expiration is set and refreshed;
- keys disappear after the inactivity window; and
- GLIDE reconnect and dependency failures produce defined errors.

The concurrency test calls the Valkey adapter from multiple threads and asserts
that the atomic script never admits more than the configured limit.

### Journey test

The documented journey:

1. starts Valkey and waits for health;
2. starts Flask;
3. sends five requests for `demo-user` and observes HTTP 200;
4. sends the sixth request and observes HTTP 429;
5. verifies rate-limit and retry metadata;
6. waits for the reported reset using bounded polling;
7. sends another request and observes HTTP 200; and
8. stops Flask and removes the Valkey container and generated state.

The default journey must complete within five minutes. CI uses a shorter
test-only window while exercising the same real script and Valkey server-time
path.

## Capsule interface

The future implementation must provide:

| Command | Responsibility |
| --- | --- |
| `make setup` | Install the pinned Python runtime and locked dependencies through uv |
| `make start` | Start Valkey, wait for health, then start Flask |
| `make verify` | Run formatting, linting, type checking, unit, integration, and journey tests |
| `make reset` | Remove rate-limit keys and restore deterministic demo state |
| `make stop` | Stop processes and remove containers and generated state |

`make stop` must remain safe after partial startup.

## Static quality gates

The implementation must run:

- Ruff formatting checks;
- Ruff lint checks;
- a configured static type checker;
- pytest unit, integration, and journey suites;
- manifest and lockfile validation;
- container and dependency scans; and
- Markdown and link checks.

All checks use pinned dependencies and run through uv where applicable.

## Security considerations

- `X-Client-ID` is untrusted demonstration input, not authentication.
- The value is bounded and hashed before key construction.
- Proxy headers are not trusted by default.
- Valkey and Flask bind to loopback.
- No credentials, tokens, or generated secrets are committed.
- Local no-auth and no-TLS behavior carries a production warning.
- Limit and window inputs are configuration, not request parameters.
- The script validates numeric arguments before changing state.
- User input cannot select arbitrary keys or commands.
- The development server is not presented as production-ready.
- The design avoids publishing performance or denial-of-service resistance
  claims.

## Resource budget

Proposed clean-clone baseline:

- 2 CPU cores;
- 2 GiB RAM;
- 2 GiB free disk;
- no paid services or credentials; and
- less than five minutes to the first complete journey.

Download size and actual peak usage must be measured during implementation and
recorded in `example.yaml`.

## Acceptance criteria

Implementation may enter review only when:

- the capsule follows the proposed path and contains no unrelated scaffolding;
- Python 3.13 is the tested baseline and uv owns dependency execution;
- Flask uses a process-lifetime GLIDE sync client;
- Valkey runs from the requested tag pinned to an immutable digest;
- the runtime path uses one atomic sorted-set script;
- five requests are allowed and the sixth is denied under the default policy;
- a real concurrent test proves that no more than the configured limit is
  admitted;
- the key expires after the rolling window;
- all response fields and failure modes are documented and tested;
- the complete journey succeeds from a clean clone;
- `make stop` leaves no running process, container, volume, or generated state;
- required security and compatibility gates pass; and
- primary and backup owners and reviewers are recorded.

## Alternatives considered

### Fixed-window counter

Rejected because it allows bursts across window boundaries and does not teach
the requested sliding-window sorted-set pattern.

### Multiple independent sorted-set commands

Rejected because concurrent workers can interleave removal, counting, and
insertion and admit too many requests.

### Optimistic transaction with retries

Rejected for the first demo because it introduces retry behavior and a larger
interface without improving the single-key atomic script.

### Token bucket

Rejected because it teaches a different algorithm and does not satisfy the
sorted-set requirement.

### Async GLIDE inside Flask routes

Rejected because Flask is a synchronous WSGI adapter for this demo. The sync
GLIDE package avoids per-request event-loop management and keeps the interface
smaller.

### Alpine-based Flask container

Rejected because the current GLIDE Python project explicitly identifies
Alpine/musl as unsupported. The requested Alpine image is used for the Valkey
server only.

## Open decisions

The following values must be recorded before implementation:

1. primary and backup content owners;
2. primary and backup Python reviewers;
3. exact Python 3.13 patch;
4. exact Flask and `valkey-glide-sync` versions;
5. resolved digest and semantic version behind `valkey/valkey:9-alpine`;
6. final request timeout and resource limits;
7. whether the initial compatibility matrix includes only standalone Valkey;
   and
8. the reviewer responsible for the clean-clone reproduction.

## Primary-source basis

- [Valkey GLIDE Python client overview](https://github.com/valkey-io/valkey-glide/blob/main/python/README.md)
- [Valkey GLIDE synchronous Lua script guide](https://github.com/valkey-io/valkey-glide/blob/main/docs/markdown/python/sync/lua-scripts-guide.md)
- [Valkey sorted-set `ZADD` documentation](https://valkey.io/commands/zadd/)
- [Valkey `ZCARD` documentation](https://valkey.io/commands/zcard/)
- [Valkey `ZREMRANGEBYSCORE` documentation](https://valkey.io/commands/zremrangebyscore/)
- [Valkey `TIME` documentation](https://valkey.io/commands/time/)
- [Valkey `PEXPIRE` documentation](https://valkey.io/commands/pexpire/)

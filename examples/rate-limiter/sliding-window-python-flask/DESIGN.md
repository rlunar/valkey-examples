# Design: Sliding-Window Rate Limiter

## Objective

Teach a true sliding-window log using Valkey sorted sets while making two
atomicity techniques directly comparable behind one Python interface.

The implementation uses Python 3.14+, uv, Flask, synchronous Valkey GLIDE, and
Valkey 9.1.1 on the pinned Trixie image. `multi-exec` is the default; `lua` is
selected through an immutable `pydantic-settings` configuration model.

## Components

```mermaid
flowchart TB
    request["HTTP request"]
    adapter["Flask adapter"]
    policy["Validated RateLimitPolicy"]
    interface["RateLimiter protocol"]
    multi["MultiExecRateLimiter"]
    script["LuaRateLimiter"]
    key["Key builder and identity hash"]
    client["GLIDE sync client"]
    zset[("Sorted set")]

    request --> adapter
    policy --> adapter
    adapter --> interface
    interface --> multi
    interface --> script
    multi --> key
    script --> key
    multi --> client
    script --> client
    client --> zset
```

The Flask layer knows only the shared decision contract. It does not know
sorted-set command order, transaction retries, script return positions, or key
layout.

## Data model

One key exists per policy and caller identity:

```text
<prefix>:<policy-id>:<sha256(identity)>
```

The raw `X-Client-ID` is never placed in a key or demo state display.

Each accepted request becomes one sorted-set member:

```text
member = <server-time-ms>:<uuidv7-request-id>
score  = <server-time-ms>
```

The UUIDv7 request ID prevents same-millisecond requests from overwriting each
other while preserving time-ordering. Denied requests are not inserted. The key
TTL is refreshed only after an accepted request, so inactive identities
disappear without a cleanup job.

## Decision semantics

For server time `now`, window `W`, and limit `L`:

1. remove scores less than or equal to `now - W`;
2. count active members;
3. accept only when the count is less than `L`;
4. on acceptance, add the unique member and set a `W` millisecond TTL;
5. read the oldest active score;
6. calculate remaining capacity and reset or retry timing.

An event exactly on the lower boundary is expired. The represented interval is
`(now - W, now]`.

## Implementation pseudocode

The following Python-like pseudocode intentionally omits GLIDE result types,
Flask response construction, logging, and defensive error handling. It shows
how the implementation fits together without replacing the runnable source.

### Startup and HTTP request

```python
settings = AppConfig()  # validates environment variables and optional .env
client = create_glide_client(settings)

if settings.implementation == "lua":
    limiter = LuaRateLimiter(client)
else:
    limiter = MultiExecRateLimiter(client)

policy = RateLimitPolicy(
    policy_id=settings.policy_id,
    limit=settings.request_limit,
    window_ms=settings.window_ms,
)


def get_limited_resource(request):
    identity = validate(request.header["X-Client-ID"])
    request_id = random_unique_id()

    try:
        decision = limiter.check(identity, policy, request_id)
    except RateLimitDependencyError:
        return json({"error": "rate-limit dependency unavailable"}, status=503)

    if decision.allowed:
        return json(decision, status=200, rate_limit_headers=decision)

    return json(
        decision,
        status=429,
        rate_limit_headers=decision,
        retry_after=decision.retry_after,
    )
```

### Shared key and decision

```python
def key_for(identity, policy):
    identity_hash = sha256(identity)
    return f"{KEY_PREFIX}:{policy.policy_id}:{identity_hash}"


def build_decision(allowed, count, oldest_timestamp, now, policy):
    reset_after = max(0, oldest_timestamp + policy.window_ms - now)

    return Decision(
        allowed=allowed,
        limit=policy.limit,
        remaining=max(0, policy.limit - count),
        reset_after_ms=reset_after,
        retry_after_ms=0 if allowed else max(1, reset_after),
    )
```

## Multi-exec implementation

```mermaid
sequenceDiagram
    autonumber
    participant app as MultiExecRateLimiter
    participant valkey as Valkey

    app->>valkey: WATCH identity key
    app->>valkey: TIME and ZCOUNT active range
    app->>app: Decide whether count is below limit
    app->>valkey: MULTI with trim and conditional add
    app->>valkey: Queue TTL, ZCARD, and oldest score
    app->>valkey: EXEC

    alt Watched key changed
        valkey-->>app: Null transaction result
        app->>app: Retry within configured bound
    else Transaction committed
        valkey-->>app: Cardinality and oldest score
        app->>app: Build shared decision
    end
```

`WATCH` closes the race between the pre-transaction count and the write. A
process-local lock is also required because `WATCH` state belongs to the GLIDE
connection. Independent clients still contend correctly through Valkey.

After `RATE_LIMIT_MAX_RETRIES` conflicts, the adapter fails closed instead of
over-admitting.

Simplified transaction pseudocode:

```python
def check(identity, policy, request_id):
    key = key_for(identity, policy)

    with connection_lock:
        for attempt in range(MAX_RETRIES):
            watch(key)

            now = valkey_time_ms()
            cutoff = now - policy.window_ms
            count = zcount(key, scores_greater_than=cutoff)
            allowed = count < policy.limit

            transaction = begin_transaction()
            transaction.remove_scores(key, up_to=cutoff)

            if allowed:
                transaction.add(
                    key,
                    member=f"{now}:{request_id}",
                    score=now,
                )
                transaction.expire(key, policy.window_ms)

            transaction.read_count(key)
            transaction.read_oldest_score(key)
            result = transaction.execute()

            if result.conflicted:
                continue

            return build_decision(
                allowed=allowed,
                count=result.count,
                oldest_timestamp=result.oldest_score,
                now=now,
                policy=policy,
            )

    raise RateLimitDependencyError("transaction retry limit exceeded")
```

## Lua implementation

```mermaid
sequenceDiagram
    autonumber
    participant app as LuaRateLimiter
    participant valkey as Valkey

    app->>valkey: Invoke cached script with key, limit, window, request ID
    valkey->>valkey: TIME, trim expired scores, and count

    alt Count is below limit
        valkey->>valkey: ZADD unique member and refresh PEXPIRE
    else Count reached limit
        valkey->>valkey: Leave denied request unrecorded
    end

    valkey->>valkey: Read oldest score and calculate timings
    valkey-->>app: allowed, limit, remaining, reset, retry
```

Valkey executes the script atomically. GLIDE retains the `Script` object so the
client can use its cached SHA and recover when the server does not yet have the
script loaded.

The real implementation is Lua, but its atomic server-side behavior can be
read as this Python-like pseudocode:

```python
def atomic_script(key, limit, window_ms, request_id):
    now = valkey_time_ms()
    cutoff = now - window_ms

    zremrangebyscore(key, negative_infinity, cutoff)
    count = zcard(key)
    allowed = count < limit

    if allowed:
        zadd(key, member=f"{now}:{request_id}", score=now)
        pexpire(key, window_ms)
        count += 1

    oldest_timestamp = first_score(key, fallback=now)
    reset_after = max(0, oldest_timestamp + window_ms - now)

    return {
        "allowed": allowed,
        "limit": limit,
        "remaining": max(0, limit - count),
        "reset_after_ms": reset_after,
        "retry_after_ms": 0 if allowed else max(1, reset_after),
    }


def check(identity, policy, request_id):
    key = key_for(identity, policy)
    result = glide.invoke_script(
        atomic_script,
        keys=[key],
        args=[policy.limit, policy.window_ms, request_id],
    )
    return Decision.from_script_result(result)
```

## HTTP and failure contract

`GET /api/limited` requires `X-Client-ID`. Responses contain `allowed`,
`limit`, `remaining`, and `reset_after_ms`; a denial also contains
`retry_after_ms`. Headers include `RateLimit-Limit`, `RateLimit-Remaining`,
`RateLimit-Reset`, and, for HTTP 429, `Retry-After`.

The API fails closed:

- invalid identity: HTTP 400;
- no trustworthy Valkey decision: HTTP 503;
- limit reached: HTTP 429;
- admitted: HTTP 200.

## Verification strategy

Unit tests cover configuration, identity hashing, decision formatting, key
construction, script-result validation, and the Flask adapter.

The real-Valkey suite runs the same contract against both adapters. It verifies
limits, identity isolation, TTLs, expiry, and HTTP behavior. Concurrency tests
use several independent GLIDE clients and assert that accepted requests and
final sorted-set cardinality never exceed the policy limit.

The interactive `make demo` uses two identities to make isolation observable,
follows repeated HTTP 429 `Retry-After` values through a bounded recovery loop,
and `make demo-record` captures that command rather than duplicating the
scenario in VHS.

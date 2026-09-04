"""Optimistic WATCH/MULTI/EXEC sliding-window implementation."""

from __future__ import annotations

from glide import Batch, GlideClient, InfBound, RangeByIndex, ScoreBoundary

from rate_limiter_demo.decision import RateLimitDecision, RateLimitPolicy
from rate_limiter_demo.limiter import RateLimitDependencyError
from rate_limiter_demo.valkey.common import (
    build_decision,
    oldest_score,
    rate_limit_key,
    server_time_ms,
)


class MultiExecRateLimiter:
    """Use an optimistic Valkey transaction for one atomic decision."""

    def __init__(self, client: GlideClient, key_prefix: str, max_retries: int) -> None:
        self._client = client
        self._key_prefix = key_prefix
        self._max_retries = max_retries

    async def check(
        self, identity: str, policy: RateLimitPolicy, request_id: str
    ) -> RateLimitDecision:
        key = rate_limit_key(self._key_prefix, policy, identity)

        for _attempt in range(self._max_retries):
            watched = False
            try:
                await self._client.watch([key])
                watched = True
                now_ms = await server_time_ms(self._client)
                cutoff_ms = now_ms - policy.window_ms
                active_count = await self._client.zcount(
                    key,
                    ScoreBoundary(cutoff_ms, is_inclusive=False),
                    InfBound.POS_INF,
                )
                allowed = active_count < policy.limit

                transaction = Batch(is_atomic=True)
                transaction.zremrangebyscore(
                    key,
                    InfBound.NEG_INF,
                    ScoreBoundary(cutoff_ms),
                )
                if allowed:
                    member = f"{now_ms}:{request_id}"
                    transaction.zadd(key, {member: float(now_ms)})
                    transaction.pexpire(key, policy.window_ms)
                transaction.zcard(key)
                transaction.zrange_withscores(key, RangeByIndex(0, 0))

                result = await self._client.exec(transaction, raise_on_error=True)
                watched = False
                if result is None:
                    continue

                result_count_raw = result[-2]
                if not isinstance(result_count_raw, int):
                    raise ValueError("Valkey transaction returned an invalid cardinality")
                result_count = result_count_raw
                result_oldest = oldest_score(result[-1], now_ms)
                return build_decision(
                    allowed=allowed,
                    policy=policy,
                    active_count=result_count,
                    now_ms=now_ms,
                    oldest_ms=result_oldest,
                )
            except Exception as error:
                raise RateLimitDependencyError(
                    "Valkey transaction could not produce a decision"
                ) from error
            finally:
                if watched:
                    await self._client.unwatch()

        raise RateLimitDependencyError(
            f"Valkey transaction conflicted more than {self._max_retries} times"
        )

    async def ping(self) -> None:
        await self._client.ping()

    async def close(self) -> None:
        await self._client.close()

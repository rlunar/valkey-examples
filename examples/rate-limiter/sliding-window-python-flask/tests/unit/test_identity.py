from __future__ import annotations

import pytest

from rate_limiter_demo.identity import InvalidIdentity, hash_identity


def test_hash_is_stable_and_does_not_reveal_identity() -> None:
    digest = hash_identity(" customer-123 ")

    assert digest == hash_identity("customer-123")
    assert len(digest) == 64
    assert "customer" not in digest


@pytest.mark.parametrize("identity", ["", "   ", "x" * 129])
def test_rejects_missing_or_unbounded_identity(identity: str) -> None:
    with pytest.raises(InvalidIdentity):
        hash_identity(identity)

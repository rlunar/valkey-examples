"""Safe identity handling for Valkey keys."""

from __future__ import annotations

import hashlib

MAX_IDENTITY_LENGTH = 128


class InvalidIdentity(ValueError):
    """Raised when a caller identity is missing or unbounded."""


def normalize_identity(identity: str) -> str:
    normalized = identity.strip()
    if not normalized:
        raise InvalidIdentity("X-Client-ID must not be empty")
    if len(normalized) > MAX_IDENTITY_LENGTH:
        raise InvalidIdentity(f"X-Client-ID must be at most {MAX_IDENTITY_LENGTH} characters")
    return normalized


def hash_identity(identity: str) -> str:
    normalized = normalize_identity(identity)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

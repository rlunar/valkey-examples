"""Pydantic response models shared by routes and tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from valkey_flask_demo.config import Topology


class CounterSnapshot(BaseModel):
    """Current value of one validated demo counter."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    value: int = Field(ge=0)
    topology: Topology


class TopologySnapshot(BaseModel):
    """Safe connection details suitable for an HTTP response."""

    model_config = ConfigDict(frozen=True)

    topology: Topology
    configured_addresses: tuple[str, ...]
    client: str
    sentinel_master: str | None = None
    discovered_primary: str | None = None

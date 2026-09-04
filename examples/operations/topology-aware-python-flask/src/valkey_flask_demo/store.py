"""Topology-aware Valkey access behind a small counter-store interface."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from threading import RLock
from typing import Protocol, TypeVar

from glide_sync import (
    AdvancedGlideClientConfiguration,
    AdvancedGlideClusterClientConfiguration,
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    GlideError,
    NodeAddress,
    NodeDiscoveryMode,
    ProtocolVersion,
)

from valkey_flask_demo.config import Address, AppSettings, Topology
from valkey_flask_demo.models import TopologySnapshot

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")
type DataClient = GlideClient | GlideClusterClient


class CounterStore(Protocol):
    """Interface consumed by the Flask adapter."""

    def get(self, name: str) -> int: ...

    def increment(self, name: str) -> int: ...

    def delete(self, name: str) -> bool: ...

    def ping(self) -> None: ...

    def topology_snapshot(self) -> TopologySnapshot: ...

    def close(self) -> None: ...


class ValkeyUnavailable(RuntimeError):
    """The selected Valkey topology could not complete an operation."""


class ValkeyStore:
    """Own one GLIDE client and hide topology-specific connection behavior."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._sentinel_lock = RLock()
        self._discovered_primary: Address | None = None
        self._client = self._connect()

    def get(self, name: str) -> int:
        value = self._run(lambda client: client.get(self._counter_key(name)))
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise ValkeyUnavailable("Counter value is not an integer") from error

    def increment(self, name: str) -> int:
        return self._run(lambda client: client.incr(self._counter_key(name)))

    def delete(self, name: str) -> bool:
        deleted = self._run(lambda client: client.delete([self._counter_key(name)]))
        return deleted > 0

    def ping(self) -> None:
        response = self._run(lambda client: client.ping())
        if response != b"PONG":
            raise ValkeyUnavailable("Valkey returned an unexpected PING response")

    def topology_snapshot(self) -> TopologySnapshot:
        primary = (
            self._format_address(self._discovered_primary)
            if self._discovered_primary is not None
            else None
        )
        client_name = (
            "GlideClusterClient" if self._settings.topology is Topology.CLUSTER else "GlideClient"
        )
        return TopologySnapshot(
            topology=self._settings.topology,
            configured_addresses=tuple(
                self._format_address(address) for address in self._settings.addresses()
            ),
            client=client_name,
            sentinel_master=(
                self._settings.sentinel_master
                if self._settings.topology is Topology.SENTINEL
                else None
            ),
            discovered_primary=primary,
        )

    def close(self) -> None:
        self._client.close()

    def _run(self, operation: Callable[[DataClient], T]) -> T:
        if self._settings.topology is not Topology.SENTINEL:
            try:
                return operation(self._client)
            except GlideError as error:
                raise ValkeyUnavailable("Valkey operation failed") from error

        with self._sentinel_lock:
            try:
                return operation(self._client)
            except GlideError as first_error:
                LOGGER.warning(
                    "Sentinel-backed command failed; rediscovering the primary",
                    extra={"topology": Topology.SENTINEL.value},
                    exc_info=first_error,
                )
                self._replace_sentinel_client()
                try:
                    return operation(self._client)
                except GlideError as retry_error:
                    raise ValkeyUnavailable(
                        "Sentinel-backed Valkey operation failed after rediscovery"
                    ) from retry_error

    def _connect(self) -> DataClient:
        if self._settings.topology is Topology.CLUSTER:
            return GlideClusterClient.create(
                GlideClusterClientConfiguration(
                    addresses=self._node_addresses(self._settings.addresses()),
                    request_timeout=self._settings.request_timeout_ms,
                    client_name=self._settings.otel_service_name,
                    advanced_config=AdvancedGlideClusterClientConfiguration(
                        connection_timeout=self._settings.connection_timeout_ms
                    ),
                )
            )

        if self._settings.topology is Topology.SENTINEL:
            primary = self._discover_sentinel_primary()
            self._discovered_primary = primary
            return self._create_standalone_client([primary], static=True)

        return self._create_standalone_client(
            list(self._settings.addresses()),
            static=False,
        )

    def _create_standalone_client(
        self,
        addresses: list[Address],
        *,
        static: bool,
    ) -> GlideClient:
        return GlideClient.create(
            GlideClientConfiguration(
                addresses=self._node_addresses(addresses),
                request_timeout=self._settings.request_timeout_ms,
                database_id=self._settings.database_id,
                client_name=self._settings.otel_service_name,
                node_discovery_mode=(
                    NodeDiscoveryMode.STATIC if static else NodeDiscoveryMode.STANDARD
                ),
                advanced_config=AdvancedGlideClientConfiguration(
                    connection_timeout=self._settings.connection_timeout_ms
                ),
            )
        )

    def _replace_sentinel_client(self) -> None:
        old_client = self._client
        primary = self._discover_sentinel_primary()
        replacement = self._create_standalone_client([primary], static=True)
        self._client = replacement
        self._discovered_primary = primary
        old_client.close()

    def _discover_sentinel_primary(self) -> Address:
        errors: list[str] = []
        for sentinel in self._settings.addresses():
            client: GlideClient | None = None
            try:
                client = GlideClient.create(
                    GlideClientConfiguration(
                        addresses=self._node_addresses([sentinel]),
                        request_timeout=self._settings.request_timeout_ms,
                        protocol=ProtocolVersion.RESP2,
                        node_discovery_mode=NodeDiscoveryMode.STATIC,
                        advanced_config=AdvancedGlideClientConfiguration(
                            connection_timeout=self._settings.connection_timeout_ms
                        ),
                    )
                )
                response = client.custom_command(
                    [
                        "SENTINEL",
                        "GET-MASTER-ADDR-BY-NAME",
                        self._settings.sentinel_master,
                    ]
                )
                primary = self._parse_sentinel_response(response)
                LOGGER.info(
                    "Discovered Sentinel primary",
                    extra={
                        "topology": Topology.SENTINEL.value,
                        "sentinel": self._format_address(sentinel),
                        "primary": self._format_address(primary),
                    },
                )
                return primary
            except (GlideError, ValueError) as error:
                errors.append(f"{self._format_address(sentinel)}: {error}")
            finally:
                if client is not None:
                    client.close()

        detail = "; ".join(errors) if errors else "no Sentinel addresses were configured"
        raise ValkeyUnavailable(f"Sentinel could not discover a primary: {detail}")

    @staticmethod
    def _parse_sentinel_response(response: object) -> Address:
        if (
            not isinstance(response, Sequence)
            or isinstance(response, (str, bytes, bytearray))
            or len(response) != 2
        ):
            raise ValueError("Sentinel returned an invalid primary address")

        host = ValkeyStore._decode(response[0])
        port_text = ValkeyStore._decode(response[1])
        if not host:
            raise ValueError("Sentinel returned an empty primary host")
        try:
            port = int(port_text)
        except ValueError as error:
            raise ValueError("Sentinel returned an invalid primary port") from error
        if not 1 <= port <= 65_535:
            raise ValueError("Sentinel returned an out-of-range primary port")
        return host, port

    @staticmethod
    def _decode(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, str):
            return value
        raise ValueError("Valkey returned a non-text address field")

    def _counter_key(self, name: str) -> str:
        return f"{self._settings.key_prefix}:counter:{name}"

    @staticmethod
    def _node_addresses(addresses: Sequence[Address]) -> list[NodeAddress]:
        return [NodeAddress(host, port) for host, port in addresses]

    @staticmethod
    def _format_address(address: Address) -> str:
        host, port = address
        rendered_host = f"[{host}]" if ":" in host else host
        return f"{rendered_host}:{port}"

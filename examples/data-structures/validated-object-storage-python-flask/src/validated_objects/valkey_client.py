"""Connect to Valkey and persist typed Pydantic products."""

from __future__ import annotations

import os
from uuid import UUID

from dotenv import load_dotenv
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
)

from validated_objects.models import PRODUCT_ADAPTER, Product

load_dotenv()

type GlideClientType = GlideClient | GlideClusterClient


class ValkeyClient:
    """Own the GLIDE client plus typed product serialization."""

    key_prefix = "valkey-examples:validated-object:product"

    def __init__(self) -> None:
        addresses = []
        for address in os.environ["VALKEY_ADDRESSES"].split(","):
            host, port = address.strip().rsplit(":", maxsplit=1)
            addresses.append(NodeAddress(host=host, port=int(port)))

        if os.environ["VALKEY_MODE"] == "cluster":
            self.client: GlideClientType = GlideClusterClient.create(
                GlideClusterClientConfiguration(addresses=addresses)
            )
        else:
            self.client = GlideClient.create(GlideClientConfiguration(addresses=addresses))

    def save(self, product: Product) -> None:
        """Serialize and store one validated product."""

        self.client.set(self._key(product.id), PRODUCT_ADAPTER.dump_json(product))

    def get(self, product_id: UUID) -> Product | None:
        """Read and reconstruct the correct product variant."""

        stored = self.client.get(self._key(product_id))
        if stored is None:
            return None
        return PRODUCT_ADAPTER.validate_json(stored)

    def delete(self, product_id: UUID) -> bool:
        """Delete one UUID-derived product key."""

        return self.client.delete([self._key(product_id)]) > 0

    def close(self) -> None:
        """Close the underlying GLIDE client."""

        self.client.close()

    def _key(self, product_id: UUID) -> str:
        return f"{self.key_prefix}:{product_id}"

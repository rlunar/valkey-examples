"""Create the selected synchronous Valkey GLIDE client."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from glide_sync import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
)

load_dotenv()

type GlideClientType = GlideClient | GlideClusterClient


class ValkeyClient:
    """Expose one GLIDE client configured entirely by the environment."""

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

    def close(self) -> None:
        """Close the underlying GLIDE client."""

        self.client.close()

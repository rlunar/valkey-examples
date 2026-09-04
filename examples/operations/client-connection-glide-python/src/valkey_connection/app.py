"""Connect to Valkey, store one value, and read it back."""

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

type ValkeyClient = GlideClient | GlideClusterClient

DEMO_KEY = "valkey-examples:client-connection:message"


def create_client() -> ValkeyClient:
    """Create the selected GLIDE client from the trusted environment."""

    addresses = []
    for address in os.environ["VALKEY_ADDRESSES"].split(","):
        host, port = address.split(":")
        addresses.append(NodeAddress(host=host, port=int(port)))

    if os.environ["VALKEY_MODE"] == "cluster":
        return GlideClusterClient.create(GlideClusterClientConfiguration(addresses=addresses))

    return GlideClient.create(GlideClientConfiguration(addresses=addresses))


def run(client: ValkeyClient) -> str:
    """Store the configured message and print the value read from Valkey."""

    client.set(DEMO_KEY, os.environ["VALKEY_MESSAGE"])
    stored = client.get(DEMO_KEY)
    assert stored is not None
    value = stored.decode()
    print(value)
    return value


def main() -> None:
    """Create the selected client, run the demo, and close the connection."""

    client = create_client()
    try:
        run(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()

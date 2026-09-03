"""A tiny Flask application that uses the GLIDE client directly."""

from __future__ import annotations

import atexit
import os
from typing import Any

from flask import Flask, jsonify, request
from waitress import serve  # type: ignore[import-untyped]

from valkey_quickstart.valkey_client import ValkeyClient

DEMO_KEY = "valkey-examples:client-quickstart:message"


def create_app(valkey: ValkeyClient | None = None) -> Flask:
    """Create the demo application around one ValkeyClient object."""

    valkey = valkey or ValkeyClient()
    app = Flask(__name__)
    app.extensions["valkey_client"] = valkey

    @app.route("/value", methods=["GET", "POST", "DELETE"])
    def value() -> tuple[Any, int]:
        if request.method == "POST":
            stored = request.get_json()["value"]
            valkey.client.set(DEMO_KEY, stored)
            return jsonify({"value": stored}), 200

        if request.method == "DELETE":
            valkey.client.delete([DEMO_KEY])
            return jsonify({"deleted": True}), 200

        stored = valkey.client.get(DEMO_KEY)
        return jsonify({"value": stored.decode() if stored is not None else None}), 200

    return app


def main() -> None:
    """Create the client and run the local WSGI server."""

    valkey = ValkeyClient()
    atexit.register(valkey.close)
    app = create_app(valkey)
    serve(
        app,
        host=os.environ["FLASK_HOST"],
        port=int(os.environ["FLASK_PORT"]),
        threads=4,
    )


if __name__ == "__main__":
    main()

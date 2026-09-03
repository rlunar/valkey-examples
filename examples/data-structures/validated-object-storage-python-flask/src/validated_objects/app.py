"""Flask routes for validated product storage."""

from __future__ import annotations

import atexit
import json
import os
from typing import Any
from uuid import UUID

from flask import Flask, jsonify, request
from pydantic import ValidationError
from waitress import serve  # type: ignore[import-untyped]

from validated_objects.models import PRODUCT_ADAPTER
from validated_objects.valkey_client import ValkeyClient


def create_app(valkey: ValkeyClient | None = None) -> Flask:
    """Create the Flask application around one typed Valkey client."""

    valkey = valkey or ValkeyClient()
    app = Flask(__name__)
    app.extensions["valkey_client"] = valkey

    @app.get("/")
    def index() -> tuple[Any, int]:
        return jsonify(
            {"application": "validated-object-storage", "types": ["physical", "digital"]}
        ), 200

    @app.post("/products")
    def create_product() -> tuple[Any, int]:
        product = PRODUCT_ADAPTER.validate_python(request.get_json())
        valkey.save(product)
        return jsonify(PRODUCT_ADAPTER.dump_python(product, mode="json")), 201

    @app.get("/products/<uuid:product_id>")
    def get_product(product_id: UUID) -> tuple[Any, int]:
        product = valkey.get(product_id)
        if product is None:
            return jsonify({"error": "product not found"}), 404
        return jsonify(PRODUCT_ADAPTER.dump_python(product, mode="json")), 200

    @app.delete("/products/<uuid:product_id>")
    def delete_product(product_id: UUID) -> tuple[Any, int]:
        return jsonify({"deleted": valkey.delete(product_id)}), 200

    @app.errorhandler(ValidationError)
    def invalid_product(error: ValidationError) -> tuple[Any, int]:
        errors = json.loads(error.json(include_input=False, include_url=False))
        return jsonify({"errors": errors}), 422

    return app


def main() -> None:
    """Create the typed client and run the local WSGI server."""

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

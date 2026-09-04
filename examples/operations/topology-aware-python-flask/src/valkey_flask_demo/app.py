"""Flask application factory and HTTP adapter."""

from __future__ import annotations

import atexit
import logging
import time
import uuid
from typing import Annotated, Any

from flask import Flask, Response, g, jsonify, request
from opentelemetry import trace
from pydantic import Field, TypeAdapter, ValidationError
from waitress import serve  # type: ignore[import-untyped]

from valkey_flask_demo.config import AppSettings
from valkey_flask_demo.models import CounterSnapshot
from valkey_flask_demo.store import CounterStore, ValkeyStore, ValkeyUnavailable
from valkey_flask_demo.telemetry import configure_observability, instrument_flask

LOGGER = logging.getLogger(__name__)
COUNTER_NAME: TypeAdapter[str] = TypeAdapter(
    Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]
)


class FlaskDemo:
    """Own route registration and translate the store interface to HTTP."""

    def __init__(self, settings: AppSettings, store: CounterStore) -> None:
        self.settings = settings
        self.store = store
        self.app = Flask(__name__)
        self.app.config["JSON_SORT_KEYS"] = True
        self.app.extensions["counter_store"] = store
        instrument_flask(self.app, settings)
        self._register_hooks()
        self._register_routes()
        self._register_error_handlers()

    def _register_hooks(self) -> None:
        @self.app.before_request
        def begin_request() -> None:
            span_context = trace.get_current_span().get_span_context()
            g.request_id = request.headers.get("X-Request-ID") or uuid.uuid7().hex
            g.started_at = time.monotonic()
            g.trace_id = f"{span_context.trace_id:032x}" if span_context.is_valid else "0"
            g.span_id = f"{span_context.span_id:016x}" if span_context.is_valid else "0"

        @self.app.after_request
        def finish_request(response: Response) -> Response:
            duration_ms = round((time.monotonic() - g.started_at) * 1_000, 2)
            response.headers["X-Request-ID"] = g.request_id
            LOGGER.info(
                "HTTP request completed",
                extra={
                    "request_id": g.request_id,
                    "trace_id": g.trace_id,
                    "span_id": g.span_id,
                    "topology": self.settings.topology.value,
                    "operation": f"{request.method} {request.path}",
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                },
            )
            return response

    def _register_routes(self) -> None:
        self.app.add_url_rule("/", view_func=self.index, methods=["GET"])
        self.app.add_url_rule("/health/live", view_func=self.live, methods=["GET"])
        self.app.add_url_rule("/health/ready", view_func=self.ready, methods=["GET"])
        self.app.add_url_rule("/api/topology", view_func=self.topology, methods=["GET"])
        self.app.add_url_rule(
            "/api/counters/<name>",
            view_func=self.counter,
            methods=["GET", "POST", "DELETE"],
        )

    def _register_error_handlers(self) -> None:
        @self.app.errorhandler(ValidationError)
        def invalid_input(error: ValidationError) -> tuple[Response, int]:
            LOGGER.info("Request validation failed", extra={"request_id": g.request_id})
            return jsonify({"error": "counter name must match [a-z0-9][a-z0-9_-]{0,63}"}), 400

        @self.app.errorhandler(ValkeyUnavailable)
        def dependency_unavailable(error: ValkeyUnavailable) -> tuple[Response, int]:
            LOGGER.exception(
                "Valkey dependency unavailable",
                extra={
                    "request_id": g.request_id,
                    "topology": self.settings.topology.value,
                },
            )
            return jsonify({"error": "Valkey dependency unavailable"}), 503

    def index(self) -> tuple[Response, int]:
        body: dict[str, Any] = {
            "application": "valkey-topology-aware-flask-demo",
            "topology": self.settings.topology.value,
            "endpoints": {
                "topology": "/api/topology",
                "counter": "/api/counters/<name>",
                "readiness": "/health/ready",
            },
        }
        return jsonify(body), 200

    def live(self) -> tuple[Response, int]:
        return jsonify({"status": "live"}), 200

    def ready(self) -> tuple[Response, int]:
        self.store.ping()
        return jsonify({"status": "ready", "topology": self.settings.topology.value}), 200

    def topology(self) -> tuple[Response, int]:
        snapshot = self.store.topology_snapshot()
        return jsonify(snapshot.model_dump(mode="json")), 200

    def counter(self, name: str) -> tuple[Response, int]:
        validated_name = COUNTER_NAME.validate_python(name)
        if request.method == "POST":
            value = self.store.increment(validated_name)
        elif request.method == "DELETE":
            self.store.delete(validated_name)
            value = 0
        else:
            value = self.store.get(validated_name)

        snapshot = CounterSnapshot(
            name=validated_name,
            value=value,
            topology=self.settings.topology,
        )
        return jsonify(snapshot.model_dump(mode="json")), 200


def create_app(
    settings: AppSettings | None = None,
    store: CounterStore | None = None,
) -> Flask:
    """Create a configured Flask application with an injectable store."""

    runtime_settings = settings or AppSettings()
    configure_observability(runtime_settings)
    runtime_store = store or ValkeyStore(runtime_settings)
    demo = FlaskDemo(runtime_settings, runtime_store)
    return demo.app


def main() -> None:
    """Run the application with a production-style local WSGI server."""

    settings = AppSettings()
    app = create_app(settings)
    store = app.extensions["counter_store"]
    atexit.register(store.close)
    LOGGER.info(
        "Starting Flask demo",
        extra={"topology": settings.topology.value, "operation": "startup"},
    )
    serve(
        app,
        host=settings.flask_host,
        port=settings.flask_port,
        threads=settings.flask_threads,
    )


if __name__ == "__main__":
    main()

"""Structured logging and OpenTelemetry setup."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from flask import Flask
from glide_sync import (
    OpenTelemetry as GlideOpenTelemetry,
)
from glide_sync import (
    OpenTelemetryConfig as GlideOpenTelemetryConfig,
)
from glide_sync import (
    OpenTelemetryTracesConfig as GlideOpenTelemetryTracesConfig,
)
from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from valkey_flask_demo.config import AppSettings

_CONFIGURE_LOCK = Lock()
_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    """Small JSON formatter that preserves OpenTelemetry correlation fields."""

    _extra_fields = (
        "topology",
        "operation",
        "sentinel",
        "primary",
        "request_id",
        "duration_ms",
        "status_code",
    )

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", getattr(record, "otelTraceID", "0")),
            "span_id": getattr(record, "span_id", getattr(record, "otelSpanID", "0")),
            "service_name": self._service_name,
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), default=str)


def configure_observability(settings: AppSettings) -> None:
    """Configure process-wide logging and optional OTLP export once."""

    global _CONFIGURED
    with _CONFIGURE_LOCK:
        if _CONFIGURED:
            return

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(settings.log_level)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(JsonLogFormatter(settings.otel_service_name))
        root_logger.addHandler(stream_handler)

        if settings.otel_enabled:
            LoggingInstrumentor().instrument(set_logging_format=False)
            resource = Resource.create(
                {
                    "service.name": settings.otel_service_name,
                    "deployment.environment.name": "local-demo",
                    "valkey.topology": settings.topology.value,
                }
            )
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            endpoint = settings.otel_exporter_otlp_endpoint
            if endpoint:
                base_endpoint = endpoint.rstrip("/")
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base_endpoint}/v1/traces"))
                )

                logger_provider = LoggerProvider(resource=resource)
                logger_provider.add_log_record_processor(
                    BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{base_endpoint}/v1/logs"))
                )
                _logs.set_logger_provider(logger_provider)
                root_logger.addHandler(
                    LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
                )

                if not GlideOpenTelemetry.is_initialized():
                    GlideOpenTelemetry.init(
                        GlideOpenTelemetryConfig(
                            traces=GlideOpenTelemetryTracesConfig(
                                endpoint=f"{base_endpoint}/v1/traces",
                                sample_percentage=100,
                            )
                        )
                    )

        _CONFIGURED = True


def instrument_flask(app: Flask, settings: AppSettings) -> None:
    """Attach Flask request spans when observability is enabled."""

    if settings.otel_enabled:
        FlaskInstrumentor().instrument_app(app)  # type: ignore[no-untyped-call]

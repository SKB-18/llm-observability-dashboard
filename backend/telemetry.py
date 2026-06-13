"""
OpenTelemetry instrumentation setup.

Call `setup_telemetry(app)` once at startup to add OTEL tracing to FastAPI.

Traces are exported to Jaeger (OTLP/gRPC) when OTEL_EXPORTER_OTLP_ENDPOINT
is set, otherwise a console exporter is used for local development.

Environment variables (optional):
  OTEL_SERVICE_NAME          – default: "llm-observability-dashboard"
  OTEL_EXPORTER_OTLP_ENDPOINT – e.g. "http://localhost:4317"
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def setup_telemetry(app=None) -> None:
    """
    Initialise OpenTelemetry SDK and instrument FastAPI.
    Safe to call even if opentelemetry packages are missing.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.resources import Resource

        service_name = os.getenv("OTEL_SERVICE_NAME", "llm-observability-dashboard")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if otlp_endpoint:  # pragma: no cover
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                logger.info("OTEL: exporting to %s", otlp_endpoint)
            except ImportError:
                logger.warning("OTEL OTLP exporter not installed, falling back to console")
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
                logger.info("OTEL: FastAPI instrumented (service=%s)", service_name)
            except ImportError:  # pragma: no cover
                logger.warning("opentelemetry-instrumentation-fastapi not installed")

    except ImportError:  # pragma: no cover
        logger.warning("OpenTelemetry SDK not installed — tracing disabled.")


def get_tracer(name: str = "llm-observability-dashboard"):
    """Return an OTEL tracer. Safe to call without setup."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:  # pragma: no cover
        return _NoopTracer()


class _NoopTracer:  # pragma: no cover
    """Fallback when OTEL is not installed."""
    def start_as_current_span(self, name, **kw):
        from contextlib import contextmanager
        @contextmanager
        def _ctx():
            yield None
        return _ctx()

from __future__ import annotations

import logging
from typing import Any

from ares.api.config import APIConfig

logger = logging.getLogger(__name__)


class TelemetryManager:
    def __init__(self) -> None:
        self._config = APIConfig.get()
        self._enabled = bool(self._config.otel_endpoint)
        self._tracer: Any = None
        self._meter: Any = None
        self._setup()

    def _setup(self) -> None:
        if not self._enabled:
            return
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": self._config.otel_service_name})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=self._config.otel_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(__name__)
            logger.info(
                "OpenTelemetry initialized with endpoint: %s",
                self._config.otel_endpoint,
            )
        except ImportError:
            logger.warning("OpenTelemetry packages not installed. Telemetry disabled.")
            self._enabled = False
        except Exception as e:
            logger.warning("Failed to initialize OpenTelemetry: %s", e)
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def create_span(self, name: str, attributes: dict[str, Any] | None = None) -> Any:
        if not self._enabled or self._tracer is None:
            return _NoopSpan()
        return self._tracer.start_as_current_span(name, attributes=attributes)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass


class _NoopSpan:
    def __enter__(self) -> _NoopSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass


_telemetry: TelemetryManager | None = None


def get_telemetry() -> TelemetryManager:
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryManager()
    return _telemetry

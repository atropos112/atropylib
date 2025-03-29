from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

from atropylib.telemetry.utils import get_resource


def init_trace_provider(service_name: str | None = None) -> None:
    resource = get_resource(service_name)
    provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter("http://otel:4318/v1/traces")
    processor = BatchSpanProcessor(span_exporter)
    provider.add_span_processor(processor)

    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)
    AsyncioInstrumentor().instrument()
    RequestsInstrumentor().instrument()

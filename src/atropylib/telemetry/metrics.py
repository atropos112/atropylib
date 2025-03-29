from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from atropylib.telemetry.utils import get_resource


def init_meter_provider(service_name: str | None = None) -> None:
    resource = get_resource(service_name)
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint="http://otel:4318/v1/metrics"))
    meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meterProvider)

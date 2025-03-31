import datetime
import logging
from json import dumps
from typing import Any

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LogRecord
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
    SimpleLogRecordProcessor,
)

from atropylib.errors import DeveloperError
from atropylib.telemetry.logs.line_fix_handler import LineFixLoggingHandler
from atropylib.telemetry.utils import get_resource

LOGGER_PROVIDER: LoggerProvider | None = None
APP_SHUTDOWN: bool = False
HANDLER: LineFixLoggingHandler | None = None


class StructuredLogger:
    def __init__(self, name: str, ctx: dict[str, Any] | None = None):
        self._logger = logging.getLogger(name)
        self._handler_added: bool = False
        self._ctx: dict[str, Any] = ctx or {}

    def _lazy_init(self):
        global LOGGER_PROVIDER

        if not LOGGER_PROVIDER:
            raise DeveloperError("Logger provider not initialized, but it should have been via init logger provider.")

        if not self._handler_added:
            add_otlp_handler(self._logger)
            self._handler_added = True

    def bind(self, **ctx: Any) -> "StructuredLogger":
        return StructuredLogger(self._logger.name, self._ctx | ctx)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._lazy_init()
        self._logger.debug(msg, extra=self._ctx | kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._lazy_init()
        self._logger.handlers.clear()
        self._logger.info(msg, extra=self._ctx | kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._lazy_init()
        self._logger.warning(msg, extra=self._ctx | kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._lazy_init()
        self._logger.error(msg, extra=self._ctx | kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._lazy_init()
        self._logger.critical(msg, extra=self._ctx | kwargs)


def ns_to_iso_str(nanoseconds: int | None) -> str:
    if nanoseconds is None:
        return ""

    """Get an ISO 8601 string from time_ns value."""
    ts = datetime.datetime.fromtimestamp(nanoseconds / 1e9, tz=datetime.timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def log_format(record: LogRecord) -> str:
    msg = {
        "body": record.body,
        "severity": record.severity_text,
        "timestamp": ns_to_iso_str(record.timestamp),
        "attributes": dict(record.attributes) if bool(record.attributes) else None,  # type: ignore[arg-type]
    }

    return dumps(msg, indent=4) + "\n"


def shutdown_logger_provider():
    global APP_SHUTDOWN
    APP_SHUTDOWN = True

    global LOGGER_PROVIDER
    if LOGGER_PROVIDER:
        LOGGER_PROVIDER.shutdown()
        LOGGER_PROVIDER = None

    global HANDLER
    if HANDLER:
        HANDLER.close()
        HANDLER = None

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    # Remove all handlers from each logger
    for logger in loggers:
        logger.handlers.clear()


def add_otlp_handler(logger: logging.Logger):
    global LOGGER_PROVIDER, HANDLER

    if not LOGGER_PROVIDER:
        raise DeveloperError("Logger provider not initialized, but it should have been via init logger provider.")
    if not HANDLER:
        raise DeveloperError("Handler not initialized, but it should have been via init logger provider.")

    logger.addHandler(HANDLER)
    logger.setLevel(logging.INFO)


def init_logger_provider(service_name: str | None = None):
    global LOGGER_PROVIDER, HANDLER

    if not LOGGER_PROVIDER:
        resource = get_resource(service_name)
        LOGGER_PROVIDER = LoggerProvider(resource=resource)
        set_logger_provider(LOGGER_PROVIDER)

        exporter_otlp = OTLPLogExporter(endpoint="http://otel:4318/v1/logs")
        exporter_console = ConsoleLogExporter(formatter=log_format)
        LOGGER_PROVIDER.add_log_record_processor(BatchLogRecordProcessor(exporter_otlp))
        LOGGER_PROVIDER.add_log_record_processor(SimpleLogRecordProcessor(exporter_console))

    if not HANDLER:
        root = logging.getLogger()
        root.handlers.clear()

        HANDLER = LineFixLoggingHandler(level=logging.INFO, logger_provider=LOGGER_PROVIDER)
        LoggingInstrumentor().instrument(set_logging_format=False)

        root.addHandler(HANDLER)


def init_test_logger_provider():
    global LOGGER_PROVIDER, HANDLER

    if not LOGGER_PROVIDER:
        LOGGER_PROVIDER = LoggerProvider()
        set_logger_provider(LOGGER_PROVIDER)

        exporter_console = ConsoleLogExporter(formatter=log_format)
        LOGGER_PROVIDER.add_log_record_processor(SimpleLogRecordProcessor(exporter_console))

    if not HANDLER:
        root = logging.getLogger()
        root.handlers.clear()

        HANDLER = LineFixLoggingHandler(level=logging.INFO, logger_provider=LOGGER_PROVIDER)
        LoggingInstrumentor().instrument(set_logging_format=False)

        root.addHandler(HANDLER)

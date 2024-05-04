import logging
import sys
from stackprinter import format

from atro_core.logging.level import level_to_str, str_to_level
from atro_core.logging.logger_type import LoggerType
from atro_core.logging.logger_type import str_to_logger_type
from atro_core.logging.opentelemetry_setup import open_telemetry_logger_setup
from atro_core.logging.rich_setup import rich_handler
from atro_core.logging.settings import LoggerSettings

logger = logging.getLogger(__name__)


def exception_handler(exc_type, exc_value, exc_traceback): 
    logger.exception(format(exc_value))


def set_logger(settings: LoggerSettings = LoggerSettings()):
    sys.excepthook = exception_handler
    handlers = []

    types = [str_to_logger_type(type.strip()) for type in settings.type.split(";")]
    for tp in types:
        match tp:
            case LoggerType.RICH:
                handlers.append(rich_handler(str_to_level(settings.level)))
            case LoggerType.OPENTELEMETRY:
                handlers.append(
                    open_telemetry_logger_setup(
                        str_to_level(settings.level),
                        settings.otel_service_name,
                        settings.otel_instance_id,
                        settings.otel_endpoint,
                    )
                )
            case _:
                raise Exception(f"Unknown logger type: {tp}")
    logger = logging.getLogger(settings.name)
    if logger.hasHandlers():
        logger.handlers.clear()

    logging.basicConfig(
        level=level_to_str(settings.level), format=settings.msg_format, datefmt=settings.date_format, handlers=handlers
    )

    return logger

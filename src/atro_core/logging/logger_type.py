from enum import Enum


class LoggerType(Enum):
    RICH = "Rich"
    OPENTELEMETRY = "OpenTelemetry"


def str_to_logger_type(type: str) -> LoggerType:
    if type.lower() == "rich":
        return LoggerType.RICH
    elif type.lower() == "opentelemetry":
        return LoggerType.OPENTELEMETRY
    else:
        raise Exception(f"Unknown logger type: {type}")

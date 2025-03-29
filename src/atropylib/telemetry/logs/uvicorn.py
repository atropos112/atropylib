from typing import Any

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "default": {
            "class": "atropylib.telemetry.logging.line_fix_handler.LineFixLoggingHandler",
        },
        "access": {
            "class": "atropylib.telemetry.logging.line_fix_handler.LineFixLoggingHandler",
        },
        "error": {
            "class": "atropylib.telemetry.logging.line_fix_handler.LineFixLoggingHandler",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

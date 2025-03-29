import inspect
import logging

from opentelemetry.sdk._logs import LoggingHandler
from typing_extensions import override


class LineFixLoggingHandler(LoggingHandler):
    """
    A class to account for the fact that we use Logger class and need to look one stack higher to catch actual caller.
    """

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record. Skip emitting if logger is NoOp.

        The record is translated to OTel format, and then sent across the pipeline.
        """

        # WARN: It doens't work with asyncio stuff :(

        frame = inspect.stack()[-1]
        filename = frame.filename
        lineno = frame.lineno

        record.funcName = frame.function
        record.filename = filename
        record.pathname = filename
        record.lineno = lineno

        super().emit(record)

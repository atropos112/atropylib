import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    name: str = "pylog"
    type: str = "rich"
    level: int | str = logging.DEBUG
    msg_format: str = "%(message)s"
    date_format: str = "%X"
    otel_service_name: str = "pylog"
    otel_instance_id: str = "pylog"
    otel_endpoint: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="ATRO_PYLOG_",
        env_file=[(Path.home() / ".config" / "atro" / "pylog.env").as_posix(), ".env"],
        env_file_encoding="utf-8",
    )

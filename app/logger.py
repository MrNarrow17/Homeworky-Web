import logging
import sys
from functools import lru_cache
from logging import INFO, LogRecord

from pythonjsonlogger.json import JsonFormatter

from app.config import get_settings

settings = get_settings()


class CloudJSONFormatter(JsonFormatter):
    """
    Transforms standard Python log records into a format optimized
    for cloud parsers.
    """

    def add_fields(self, log_data, record: LogRecord, message_dict):
        super().add_fields(log_data, record, message_dict)

        log_data["timestamp"] = settings.current_time.isoformat()

        if "asctime" in log_data:
            del log_data["asctime"]

        if log_data.get("levelname"):
            log_data["severity"] = log_data["levelname"]
            del log_data["levelname"]


class AppLogger:
    """
    Global logger for the application.
    """

    def __init__(
        self,
        json_formatter: type[JsonFormatter] | None = None,
        name: str | None = None,
        level: int = INFO,
    ) -> None:
        self.name = name if name else settings.logger_name
        self.level = level if level else settings.log_level

        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(self.level)

        self._json_formatter = json_formatter or CloudJSONFormatter

        if not self._logger.handlers:
            self._add_json_handler()

    def _add_json_handler(self) -> None:
        json_handler = logging.StreamHandler(sys.stdout)
        log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"

        json_handler.setFormatter(self._json_formatter(fmt=log_format, timestamp=True))
        self._logger.addHandler(json_handler)

    @property
    def logger(self) -> logging.Logger:
        return self._logger


@lru_cache(maxsize=1)
def get_app_logger() -> AppLogger:
    return AppLogger()

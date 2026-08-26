import logging
import sys
import time
from functools import lru_cache
from logging import INFO, LogRecord

from fastapi import Request
from pythonjsonlogger.json import JsonFormatter
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.config import get_settings

settings = get_settings()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """

    def __init__(self, app: ASGIApp, logger: logging.Logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start_time = time.perf_counter()
        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        log_extra = {
            "http_method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": round(process_time, 4),
            "client_host": request.client.host if request.client else "unknown",
        }

        self.logger.info(
            f"Request processed: {request.method} {request.url.path}", extra=log_extra
        )

        return response


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
        json_formatter: type[JsonFormatter],
        name: str | None = None,
        level: int = INFO,
    ) -> None:
        self.name = name if name else settings.logger_name
        self.level = level if level else settings.log_level

        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(self.level)

        self._json_formatter = json_formatter

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
    return AppLogger(json_formatter=CloudJSONFormatter)

"""JSON logs on stdout, one line per event, uvicorn's, NATS's and TaskIQ's included. Every line logged while a
task runs carries its `task_id`."""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime", "color_message"}
task_id: ContextVar[str | None] = ContextVar("task_id", default=None)


class NoTaskTraceback(logging.Filter):
    """Drops TaskIQ's own line on a failed task: it repeats the exception, values included, that the worker
    already logs its way (fields in error only for an invalid message, the traceback otherwise)."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.msg != "Exception found while executing function."


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if current := task_id.get():
            entry["task_id"] = current
        entry |= {k: v for k, v in record.__dict__.items() if k not in RESERVED}
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)


def config(level: str) -> dict[str, Any]:
    """`logging` configuration shared by the application, uvicorn and the libraries."""
    handler = {"class": "logging.StreamHandler", "formatter": "json", "stream": "ext://sys.stdout"}
    loggers: dict[str, Any] = {
        name: {"handlers": ["stdout"], "level": level, "propagate": False}
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
    }
    # TaskIQ logs every execution at INFO; the worker writes its own line per task, with metrics.
    loggers["taskiq"] = {"level": "WARNING"}
    loggers["taskiq.receiver.receiver"] = {"filters": ["no_task_traceback"]}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "filters": {"no_task_traceback": {"()": NoTaskTraceback}},
        "handlers": {"stdout": handler},
        "root": {"handlers": ["stdout"], "level": level},
        "loggers": loggers,
    }

"""JSON logs on stdout, one line per event, uvicorn's included."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime", "color_message"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        entry |= {k: v for k, v in record.__dict__.items() if k not in RESERVED}
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)


def config(level: str) -> dict[str, Any]:
    """`logging` configuration shared by the application and uvicorn."""
    handler = {"class": "logging.StreamHandler", "formatter": "json", "stream": "ext://sys.stdout"}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {"stdout": handler},
        "root": {"handlers": ["stdout"], "level": level},
        "loggers": {
            name: {"handlers": ["stdout"], "level": level, "propagate": False}
            for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
        },
    }

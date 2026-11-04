"""Logging of the worker: the JSON logs of `common.logs`, NATS's and TaskIQ's lines included. Every line
logged while a task runs carries its `task_id` (`common.logs.task_id`)."""

import logging
from typing import Any

from common import logs


class NoTaskTraceback(logging.Filter):
    """Drops TaskIQ's own line on a failed task: it repeats the exception, values included, that the worker
    already logs its way (fields in error only for an invalid message, the traceback otherwise)."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.msg != "Exception found while executing function."


def config(level: str) -> dict[str, Any]:
    """`logging` configuration shared by the worker, uvicorn and the libraries."""
    base = logs.config(level)
    # TaskIQ logs every execution at INFO; the worker writes its own line per task, with metrics.
    base["loggers"]["taskiq"] = {"level": "WARNING"}
    base["loggers"]["taskiq.receiver.receiver"] = {"filters": ["no_task_traceback"]}
    base["filters"] = {"no_task_traceback": {"()": NoTaskTraceback}}
    return base

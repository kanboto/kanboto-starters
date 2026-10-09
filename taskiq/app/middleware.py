"""Per-task plumbing, as TaskIQ middlewares: task id on every log line, a timeout on every task, one log line
and metrics per execution, bounded retries and dead letters."""

import logging
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

from pydantic import ValidationError
from taskiq import BrokerMessage, TaskiqMessage, TaskiqMiddleware, TaskiqResult
from taskiq.kicker import AsyncKicker

from app import logs, metrics
from app.config import get_settings

log = logging.getLogger("app.tasks")
started: ContextVar[float] = ContextVar("started")


class Unreadable(Exception):
    """A message the worker cannot run: not a task message, or a task it does not know."""


def describe(error: BaseException) -> str:
    """What went wrong, for logs and dead letters, without the message's values (maybe personal data)."""
    if isinstance(error, ValidationError):
        fields = sorted({".".join(map(str, e["loc"])) for e in error.errors()})
        return f"invalid fields: {', '.join(fields)}"
    if isinstance(error, Unreadable):
        return str(error)
    return " ".join(repr(error).split())[:1000]


def attempt(message: TaskiqMessage) -> int:
    """1 for the first execution of a task, then 2, 3... for its retries."""
    return int(message.labels.get("attempt", 1))


class Observe(TaskiqMiddleware):
    """Each execution runs in its own asyncio task: what is set here is seen by the task and by no other."""

    def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        logs.task_id.set(message.task_id)
        started.set(time.perf_counter())
        # A task may set its own `timeout` label; every other one is bounded by TASK_TIMEOUT_S.
        message.labels.setdefault("timeout", get_settings().task_timeout_s)
        return message

    def post_execute(self, message: TaskiqMessage, result: TaskiqResult[Any]) -> None:
        duration = time.perf_counter() - started.get()
        status = "failed" if result.is_err else "succeeded"
        metrics.observe(message.task_name, status, duration)
        log.info(
            "task",
            extra={
                "task": message.task_name,
                "attempt": attempt(message),
                "status": status,
                "duration_ms": round(duration * 1000, 1),
            },
        )


DeadLetter = Callable[[BrokerMessage, BaseException], Awaitable[None]]


class Retry(TaskiqMiddleware):
    """A failed task is published again, as a new message, up to MAX_RETRIES times; after its last attempt it
    is handed to `dead_letter`, so it is kept, never dropped. An invalid message is dead-lettered at once:
    sending it again would not make it valid.

    The failed message is acknowledged only once its retry or dead letter is published: if publishing fails,
    JetStream delivers the message again.
    """

    def __init__(self, dead_letter: DeadLetter) -> None:
        super().__init__()
        self.dead_letter = dead_letter

    async def on_error(
        self, message: TaskiqMessage, result: TaskiqResult[Any], exception: BaseException
    ) -> None:
        current = attempt(message)
        extra = {"task": message.task_name, "attempt": current, "error": describe(exception)}
        # The application's own failures keep their traceback; an invalid message has nothing to show but its
        # fields in error.
        trace = None if isinstance(exception, ValidationError) else exception
        if trace is None:
            log.error("task rejected, invalid message, dead-lettered", extra=extra)
        elif current <= get_settings().max_retries:
            log.warning("task failed, retrying", extra=extra, exc_info=trace)
            kicker: AsyncKicker[Any, Any] = AsyncKicker(message.task_name, self.broker, dict(message.labels))
            await (
                kicker.with_task_id(message.task_id)
                .with_labels(attempt=current + 1)
                .kiq(*message.args, **message.kwargs)
            )
            return
        else:
            log.error("task failed on its last attempt, dead-lettered", extra=extra, exc_info=trace)
        await self.dead_letter(self.broker.formatter.dumps(message), exception)
        metrics.DEAD_LETTERS.labels(message.task_name).inc()

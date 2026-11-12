"""Runs one task under the contract every scheduled task gets: one run at a time, a bounded duration, one log
line for the outcome and an exit code the platform reads (0: done, 1: failed, 2: unknown task, 3: another run
still holds the lock). Without a name, `check()` loads every task and exits.

The lock is a PostgreSQL advisory lock on the task's name, held for the whole run, when the database is
configured; the platform never starts two runs of a task at once, the lock also covers manual runs."""

import asyncio
import importlib
import logging
import pkgutil
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from sqlalchemy import text

from common import db, logs

from .config import get_settings

log = logging.getLogger(__package__)

DONE, FAILED, UNKNOWN, LOCKED = 0, 1, 2, 3


class Locked(Exception):
    pass


def find(name: str) -> Callable[[], Awaitable[None]] | None:
    """The task's `run()`, or None when no module `jobs/<name>.py` defines one."""
    if not name.isidentifier():
        return None
    try:
        module = importlib.import_module(f"{__package__}.jobs.{name}")
    except ModuleNotFoundError as exc:
        if exc.name == f"{__package__}.jobs.{name}":
            return None
        raise
    found = getattr(module, "run", None)
    return found if callable(found) else None


def check() -> int:
    """Loads every module of `jobs/` and logs the tasks found: the image's default command, which proves it
    starts and its tasks import. 1 when a module has no `run()`."""
    jobs = importlib.import_module(f"{__package__}.jobs")
    names = sorted(m.name for m in pkgutil.iter_modules(jobs.__path__) if not m.name.startswith("_"))
    broken = [name for name in names if find(name) is None]
    if broken:
        log.error("tasks without run()", extra={"tasks": broken})
        return FAILED
    log.info("tasks", extra={"tasks": names})
    return DONE


@asynccontextmanager
async def lock(name: str) -> AsyncIterator[None]:
    """Holds the task's advisory lock on its own connection, released when the run ends (or the connection
    drops). Without a PostgreSQL database, nothing to hold."""
    if not db.configured() or db.engine().dialect.name != "postgresql":
        yield
        return
    async with db.engine().connect() as connection:
        key = f"task:{name}"
        taken = await connection.scalar(text("SELECT pg_try_advisory_lock(hashtext(:key))"), {"key": key})
        if not taken:
            raise Locked
        try:
            yield
        finally:
            await connection.execute(text("SELECT pg_advisory_unlock(hashtext(:key))"), {"key": key})


async def run(name: str) -> int:
    task = find(name)
    if task is None:
        log.error("unknown task", extra={"task": name})
        return UNKNOWN
    token = logs.task_id.set(uuid.uuid4().hex)
    started = time.monotonic()
    outcome, code = "done", DONE
    try:
        async with lock(name), asyncio.timeout(get_settings().task_timeout_s):
            await task()
    except Locked:
        outcome, code = "locked", LOCKED
    except TimeoutError:
        outcome, code = "timed out", FAILED
    except Exception:
        log.exception("task failed", extra={"task": name})
        outcome, code = "failed", FAILED
    finally:
        await db.dispose()
        log.info(
            "task",
            extra={"task": name, "outcome": outcome, "duration_s": round(time.monotonic() - started, 3)},
        )
        logs.task_id.reset(token)
    return code

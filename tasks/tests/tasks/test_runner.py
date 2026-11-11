import asyncio
import json
import logging
import sys
import types
from collections.abc import Iterator

import pytest
from sqlalchemy import text

from common import db, logs
from tasks import runner
from tasks.config import get_settings


@pytest.fixture(autouse=True)
def settings(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    monkeypatch.setenv("TASK_TIMEOUT_S", "0.2")
    caplog.set_level(logging.INFO)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def job(name: str, body: types.FunctionType) -> None:
    """Registers `tasks.jobs.<name>` for the test, as if `jobs/<name>.py` existed."""
    module = types.ModuleType(f"tasks.jobs.{name}")
    module.run = body  # type: ignore[attr-defined]
    sys.modules[module.__name__] = module


@pytest.fixture(autouse=True)
def forget_jobs() -> Iterator[None]:
    before = set(sys.modules)
    yield
    for name in set(sys.modules) - before:
        if name.startswith("tasks.jobs."):
            del sys.modules[name]


def outcome(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    """The run's outcome line, as written to stdout."""
    record = next(r for r in caplog.records if r.getMessage() == "task")
    return json.loads(logs.JsonFormatter().format(record))  # type: ignore[no-any-return]


async def done() -> None:
    logging.getLogger("tasks.jobs.tidy").info("tidied")


async def test_a_task_runs_and_logs_its_outcome(no_database: None, caplog: pytest.LogCaptureFixture) -> None:
    job("tidy", done)  # type: ignore[arg-type]
    assert await runner.run("tidy") == runner.DONE
    line = outcome(caplog)
    assert line["task"] == "tidy" and line["outcome"] == "done"
    assert "tidied" in caplog.messages


async def test_a_failing_task_exits_non_zero(no_database: None, caplog: pytest.LogCaptureFixture) -> None:
    async def fails() -> None:
        raise RuntimeError("boom")

    job("fails", fails)  # type: ignore[arg-type]
    assert await runner.run("fails") == runner.FAILED
    assert outcome(caplog)["outcome"] == "failed"


async def test_a_run_over_its_timeout_is_stopped(no_database: None, caplog: pytest.LogCaptureFixture) -> None:
    async def hangs() -> None:
        await asyncio.sleep(5)

    job("hangs", hangs)  # type: ignore[arg-type]
    assert await runner.run("hangs") == runner.FAILED
    assert outcome(caplog)["outcome"] == "timed out"


@pytest.mark.parametrize("name", ["missing", "../etc", "runner"])
async def test_an_unknown_task_is_refused(no_database: None, name: str) -> None:
    assert await runner.run(name) == runner.UNKNOWN


async def test_a_second_run_waits_for_the_first(database: None) -> None:
    """On PostgreSQL, a run whose lock is held elsewhere stops at once; the holder's run is untouched."""
    if db.engine().dialect.name != "postgresql":
        pytest.skip("advisory locks need PostgreSQL")
    job("tidy", done)  # type: ignore[arg-type]
    async with db.engine().connect() as holder:
        await holder.execute(text("SELECT pg_advisory_lock(hashtext('task:tidy'))"))
        assert await runner.run("tidy") == runner.LOCKED
        await holder.execute(text("SELECT pg_advisory_unlock(hashtext('task:tidy'))"))
    assert await runner.run("tidy") == runner.DONE

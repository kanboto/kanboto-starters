"""Tasks and their plumbing: one log line per execution, metrics, timeout, retries and dead letters."""

import asyncio
import json
import logging
import logging.config

import pytest
from prometheus_client import REGISTRY
from pydantic import ValidationError
from taskiq import BrokerMessage

from app import logs, tasks
from app.config import get_settings
from app.tasks import Item
from tests.conftest import Memory


def _count(name: str, **labels: str) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0


def _records(caplog: pytest.LogCaptureFixture, message: str) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage() == message]


ITEM = {"id": "42", "name": "Widget", "quantity": 2, "tags": ["new"]}


async def test_process_item_travels_as_json_and_comes_back_as_a_model(
    memory: Memory, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app")
    wire: list[bytes] = []
    kick = memory.kick

    async def record(message: BrokerMessage) -> None:
        wire.append(message.message)
        await kick(message)

    received: list[object] = []
    original = tasks.process_item.original_func

    async def spy(item: Item) -> None:
        received.append(item)
        await original(item)

    monkeypatch.setattr(memory, "kick", record)
    memory.register_task(spy, task_name="process_item")
    before = _count("tasks_total", task="process_item", status="succeeded")
    task = memory.find_task("process_item")
    assert task is not None
    sent = await task.kiq(Item(**ITEM))
    await memory.settle()

    [message] = wire
    assert json.loads(message)["args"] == [ITEM]  # JSON on the wire
    assert received == [Item(**ITEM)] and isinstance(received[0], Item)  # a model in the task
    [line] = _records(caplog, "item processed")
    assert line.__dict__["item_id"] == "42" and line.__dict__["quantity"] == 2
    [execution] = _records(caplog, "task")
    assert execution.__dict__["status"] == "succeeded" and execution.__dict__["attempt"] == 1
    assert _count("tasks_total", task="process_item", status="succeeded") == before + 1
    assert not memory.dead_letters and sent.task_id


async def test_invalid_message_is_dead_lettered_without_retry(
    memory: Memory, caplog: pytest.LogCaptureFixture
) -> None:
    task = memory.find_task("process_item")
    assert task is not None
    await task.kiq(item={"id": "42", "name": "secret name", "quantity": 0})
    await memory.settle()

    [(message, error)] = memory.dead_letters
    assert message.task_name == "process_item" and isinstance(error, ValidationError)
    [rejected] = _records(caplog, "task rejected, invalid message, dead-lettered")
    assert rejected.__dict__["error"] == "invalid fields: quantity" and rejected.__dict__["attempt"] == 1
    assert "secret name" not in caplog.text


async def test_log_lines_carry_the_task_id(memory: Memory, capsys: pytest.CaptureFixture[str]) -> None:
    logging.config.dictConfig(logs.config("INFO"))
    task = memory.find_task("process_item")
    assert task is not None
    sent = await task.kiq(Item(id="7", name="Bolt", quantity=1))
    await memory.settle()
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    [processed] = [line for line in lines if line["message"] == "item processed"]
    assert processed["task_id"] == sent.task_id and processed["item_id"] == "7"


async def test_failed_task_is_retried_then_dead_lettered(
    memory: Memory, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(get_settings(), "max_retries", 2)
    caplog.set_level(logging.INFO, logger="app")
    calls: list[str] = []

    async def always_fails(item_id: str) -> None:
        calls.append(item_id)
        raise RuntimeError("boom")

    task = memory.register_task(always_fails, task_name="always_fails")
    before = _count("tasks_total", task="always_fails", status="failed")
    await task.kiq(item_id="1")
    await memory.settle()

    assert calls == ["1", "1", "1"]  # the first attempt and MAX_RETRIES retries
    assert [r.__dict__["attempt"] for r in _records(caplog, "task failed, retrying")] == [1, 2]
    [last] = _records(caplog, "task failed on its last attempt, dead-lettered")
    assert last.__dict__["attempt"] == 3
    [(message, error)] = memory.dead_letters
    assert message.task_name == "always_fails" and isinstance(error, RuntimeError)
    assert memory.formatter.loads(message.message).kwargs == {"item_id": "1"}
    assert _count("tasks_dead_lettered_total", task="always_fails") == 1
    # Each attempt is an execution: three failures, three durations.
    assert _count("tasks_total", task="always_fails", status="failed") == before + 3
    assert _count("task_duration_seconds_count", task="always_fails") == 3


async def test_task_that_recovers_is_not_dead_lettered(memory: Memory) -> None:
    calls = 0

    async def flaky() -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ConnectionError("transient")

    task = memory.register_task(flaky, task_name="flaky")
    await task.kiq()
    await memory.settle()
    assert calls == 2 and not memory.dead_letters


async def test_tasks_are_bounded_by_a_timeout(memory: Memory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "task_timeout_s", 0.05)
    monkeypatch.setattr(get_settings(), "max_retries", 0)

    async def stuck() -> None:
        await asyncio.sleep(10)

    task = memory.register_task(stuck, task_name="stuck")
    await task.kiq()
    await asyncio.wait_for(memory.settle(), 2)
    [(_, error)] = memory.dead_letters
    assert isinstance(error, TimeoutError)

"""The worker process: probes, metrics, acknowledgements, bounded concurrency and graceful shutdown."""

import asyncio
import logging
import logging.config
import os
import signal
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from taskiq import BrokerMessage, TaskiqMessage

from app import health, logs, tasks, worker
from app.config import get_settings
from tests.conftest import QueueBroker


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=health.app), base_url="http://test") as c:
        yield c


async def test_probes(client: AsyncClient) -> None:
    assert (await client.get("/healthz")).status_code == 200
    unready = await client.get("/readyz")
    assert unready.status_code == 503 and unready.json() == {"status": "unavailable"}
    health.State.connected = lambda: True
    assert (await client.get("/readyz")).status_code == 200
    health.State.connected = lambda: False
    assert (await client.get("/readyz")).status_code == 503
    health.State.connected = lambda: True
    health.State.stopping = True
    stopping = await client.get("/readyz")
    assert stopping.status_code == 503 and stopping.json() == {"status": "stopping"}
    assert (await client.get("/api")).status_code == 404
    assert (await client.post("/healthz")).status_code == 405


async def test_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/plain")
    for metric in ("tasks_total", "task_duration_seconds", "tasks_dead_lettered_total", "python_gc_objects"):
        assert f"# TYPE {metric}" in response.text


async def _started(event: asyncio.Event) -> None:
    await asyncio.wait_for(event.wait(), 2)


async def test_shutdown_lets_in_flight_tasks_complete(queue_broker: QueueBroker) -> None:
    started, release = asyncio.Event(), asyncio.Event()

    async def slow() -> None:
        started.set()
        await release.wait()

    task = queue_broker.register_task(slow, task_name="slow")
    stop = asyncio.Event()
    consumer = asyncio.create_task(worker.consume(queue_broker, stop))
    first = await task.kiq()
    await _started(started)
    assert health.State.connected is not None and health.State.connected()

    stop.set()
    second = await task.kiq()  # published after the stop: left in the queue for another instance
    await asyncio.sleep(0.05)
    assert not consumer.done() and queue_broker.acked == []
    release.set()
    await asyncio.wait_for(consumer, 2)
    assert queue_broker.acked == [first.task_id] and second.task_id not in queue_broker.acked
    assert queue_broker.queue.qsize() == 1 and health.State.connected is None


async def test_task_over_the_shutdown_timeout_is_not_acknowledged(
    queue_broker: QueueBroker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "shutdown_timeout_s", 0.1)
    started = asyncio.Event()

    async def stuck() -> None:
        started.set()
        await asyncio.sleep(10)

    task = queue_broker.register_task(stuck, task_name="stuck")
    stop = asyncio.Event()
    consumer = asyncio.create_task(worker.consume(queue_broker, stop))
    await task.kiq()
    await _started(started)
    stop.set()
    await asyncio.wait_for(consumer, 2)
    assert queue_broker.acked == []  # JetStream delivers it again


async def test_concurrency_is_bounded(queue_broker: QueueBroker, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "worker_concurrency", 2)
    running, peak, release = 0, 0, asyncio.Event()

    async def work() -> None:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await release.wait()
        running -= 1

    task = queue_broker.register_task(work, task_name="work")
    stop = asyncio.Event()
    consumer = asyncio.create_task(worker.consume(queue_broker, stop))
    for _ in range(5):
        await task.kiq()
    await asyncio.sleep(0.1)
    assert peak == 2
    release.set()
    await asyncio.sleep(0.1)
    stop.set()
    await asyncio.wait_for(consumer, 2)
    assert len(queue_broker.acked) == 5


async def test_sigterm_stops_gracefully(queue_broker: QueueBroker, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "port", 0)
    started, release = asyncio.Event(), asyncio.Event()

    async def slow() -> None:
        started.set()
        await release.wait()

    task = queue_broker.register_task(slow, task_name="slow")
    run = asyncio.create_task(worker.run(queue_broker))
    sent = await task.kiq()
    await _started(started)
    os.kill(os.getpid(), signal.SIGTERM)
    await asyncio.sleep(0.05)
    assert health.State.stopping and not run.done()  # unready at once, the in-flight task still runs
    release.set()
    await asyncio.wait_for(run, 5)
    assert queue_broker.acked == [sent.task_id]


async def test_messages_the_worker_cannot_run_are_dead_lettered(
    queue_broker: QueueBroker, caplog: pytest.LogCaptureFixture
) -> None:
    """TaskIQ would drop them and log their content: they are kept, their content out of the logs."""
    unknown = queue_broker.formatter.dumps(
        TaskiqMessage(task_id="t1", task_name="gone", labels={}, args=[], kwargs={})
    )
    await queue_broker.kick(BrokerMessage(task_id="t0", task_name="", message=b"secret, not json", labels={}))
    await queue_broker.kick(unknown)
    stop = asyncio.Event()
    consumer = asyncio.create_task(worker.consume(queue_broker, stop))
    await queue_broker.wait_acked(2)
    stop.set()
    await asyncio.wait_for(consumer, 2)

    assert queue_broker.acked == ["t0", "t1"]
    assert [(m.message, m.task_name, str(e)) for m, e in queue_broker.dead_letters] == [
        (b"secret, not json", "unknown", "not a task message"),
        (unknown.message, "gone", "unknown task"),
    ]
    assert "secret" not in caplog.text


async def test_invalid_arguments_are_logged_without_their_values(
    queue_broker: QueueBroker, capsys: pytest.CaptureFixture[str]
) -> None:
    logging.config.dictConfig(logs.config("INFO"))
    queue_broker.register_task(tasks.process_item.original_func, task_name="process_item")
    task = queue_broker.find_task(
        "process_item"
    )  # untyped: the message is sent as it would come from elsewhere
    assert task is not None
    sent = await task.kiq(item={"id": "1", "name": "secret name", "quantity": 0})
    stop = asyncio.Event()
    consumer = asyncio.create_task(worker.consume(queue_broker, stop))
    await queue_broker.wait_acked(1)
    stop.set()
    await asyncio.wait_for(consumer, 2)

    out = capsys.readouterr().out
    assert queue_broker.acked == [sent.task_id] and len(queue_broker.dead_letters) == 1
    assert "invalid fields: quantity" in out and "secret name" not in out and "input_value" not in out

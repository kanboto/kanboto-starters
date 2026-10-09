"""The worker: one asyncio process consumes tasks from JetStream and serves the probes and metrics on `PORT`.

Shutdown on SIGTERM (or SIGINT), in order: `/readyz` fails at once, no new task is fetched, in-flight tasks
get `SHUTDOWN_TIMEOUT_S` to complete and be acknowledged, then the NATS connection and the HTTP server close.
A task still running then is not acknowledged: JetStream delivers it again. A second signal stops at once.
"""

import asyncio
import contextlib
import logging
import signal
from collections.abc import Awaitable, Iterator

import uvicorn
from taskiq import AckableMessage, AsyncBroker, BrokerMessage
from taskiq.acks import AcknowledgeType
from taskiq.receiver import Receiver
from taskiq.utils import maybe_awaitable
from taskiq_nats.broker import BaseJetStreamBroker

from app import health, logs, metrics
from app import tasks as _tasks  # noqa: F401  registers the tasks on the broker
from app.broker import broker as default_broker
from app.config import get_settings
from app.middleware import Retry, Unreadable

log = logging.getLogger("app")
# After a consumer error (lost connection), pause before fetching again.
RESTART_DELAY_S = 1


class Gate(Receiver):
    """TaskIQ's receiver, minus its habit of dropping what it cannot run: a message that is not a task
    message, or that names an unknown task, is dead-lettered (and its content kept out of the logs)."""

    async def callback(self, message: bytes | AckableMessage, raise_err: bool = False) -> None:
        data = message.data if isinstance(message, AckableMessage) else message
        try:
            parsed = self.broker.formatter.loads(message=data)
            parsed.parse_labels()
            error = None if self.broker.find_task(parsed.task_name) else Unreadable("unknown task")
            name = parsed.task_name
        except Exception:
            error, name = Unreadable("not a task message"), "unknown"
        if error is None:
            await super().callback(message, raise_err)
            return
        log.error("message rejected, dead-lettered", extra={"task": name, "error": str(error)})
        dead_letter = next(m for m in self.broker.middlewares if isinstance(m, Retry)).dead_letter
        await dead_letter(BrokerMessage(task_id="", task_name=name, message=data, labels={}), error)
        metrics.DEAD_LETTERS.labels(name).inc()
        if isinstance(message, AckableMessage):
            await maybe_awaitable(message.ack())


class HttpServer(uvicorn.Server):
    """Uvicorn without its own signal handling: the worker handles signals and stops the server last."""

    @contextlib.contextmanager
    def capture_signals(self) -> Iterator[None]:
        yield


async def _unless_stopped(awaitable: Awaitable[object], stop: asyncio.Event) -> bool:
    """Awaits `awaitable` unless `stop` is set first, in which case it is cancelled. True if it completed."""
    work = asyncio.ensure_future(awaitable)
    stopped = asyncio.create_task(stop.wait())
    await asyncio.wait({work, stopped}, return_when=asyncio.FIRST_COMPLETED)
    stopped.cancel()
    if work.done():
        work.result()
        return True
    work.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await work
    return False


def _connected(broker: AsyncBroker) -> bool:
    return not isinstance(broker, BaseJetStreamBroker) or broker.client.is_connected


async def consume(broker: AsyncBroker, stop: asyncio.Event) -> None:
    """Runs tasks until `stop` is set, then waits for the in-flight ones within SHUTDOWN_TIMEOUT_S."""
    settings = get_settings()
    broker.is_worker_process = True
    try:
        # Connects, waiting for NATS as long as needed, then sets up the stream and the consumer.
        if not await _unless_stopped(broker.startup(), stop):
            return
        health.State.connected = lambda: _connected(broker)
        receiver = Gate(
            broker,
            max_async_tasks=settings.worker_concurrency,
            # Each task validates its own arguments: TaskIQ would only log the invalid values and go on.
            validate_params=False,
            run_startup=False,
            ack_type=AcknowledgeType.WHEN_SAVED,
            wait_tasks_timeout=settings.shutdown_timeout_s,
        )
        log.info("consuming", extra={"concurrency": settings.worker_concurrency})
        while not stop.is_set():
            try:
                await receiver.listen(stop)
            except Exception as exc:
                log.warning("consumer error, restarting", extra={"error": repr(exc)})
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), RESTART_DELAY_S)
    finally:
        health.State.connected = None
        await broker.shutdown()


async def run(broker: AsyncBroker = default_broker) -> None:
    settings = get_settings()
    stop = asyncio.Event()
    consumer = asyncio.create_task(consume(broker, stop))

    def on_signal(sig: signal.Signals) -> None:
        if health.State.stopping:
            log.warning("stopping now", extra={"signal": sig.name})
            consumer.cancel()
            return
        log.info("stopping", extra={"signal": sig.name, "timeout_s": settings.shutdown_timeout_s})
        health.State.stopping = True
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, on_signal, sig)
    server = HttpServer(
        uvicorn.Config(
            health.app,
            host="0.0.0.0",
            port=settings.port,
            log_config=logs.config(settings.log_level),
            access_log=False,
            lifespan="off",
            server_header=False,
        )
    )
    http = asyncio.create_task(server.serve())
    log.info("starting")
    try:
        with contextlib.suppress(asyncio.CancelledError):
            await consumer
    finally:
        server.should_exit = True
        await http
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.remove_signal_handler(sig)
    log.info("stopped")

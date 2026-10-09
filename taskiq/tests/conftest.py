import asyncio
import functools
import os
from collections.abc import AsyncGenerator, AsyncIterator, Iterator

import pytest
from taskiq import AckableMessage, AsyncBroker, BrokerMessage, InMemoryBroker

# No NATS server in tests: the real broker is created at import but never connected.
os.environ.setdefault("NATS_URL", "nats://localhost:4222")

from app import health, tasks  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.middleware import Observe, Retry  # noqa: E402


@pytest.fixture(autouse=True)
def settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    health.State.stopping = False
    health.State.connected = None


class Memory(InMemoryBroker):
    """Runs tasks in process, with the worker's middlewares; dead letters are kept in a list."""

    def __init__(self) -> None:
        super().__init__()
        self.dead_letters: list[tuple[BrokerMessage, BaseException]] = []
        self.add_middlewares(Observe(), Retry(self.dead_letter))
        self.register_task(tasks.process_item.original_func, task_name="process_item")

    async def dead_letter(self, message: BrokerMessage, error: BaseException) -> None:
        self.dead_letters.append((message, error))

    async def settle(self) -> None:
        """Waits for every task, retries included."""
        while any(not task.done() for task in self._running_tasks):
            await self.wait_all()


@pytest.fixture
async def memory() -> AsyncIterator[Memory]:
    broker = Memory()
    await broker.startup()
    yield broker
    await broker.shutdown()


class QueueBroker(AsyncBroker):
    """A broker with acknowledgements, as JetStream's, over an in-process queue."""

    def __init__(self) -> None:
        super().__init__()
        self.queue: asyncio.Queue[BrokerMessage] = asyncio.Queue()
        self.acked: list[str] = []
        self.ack_seen = asyncio.Event()
        self.dead_letters: list[tuple[BrokerMessage, BaseException]] = []
        self.add_middlewares(Observe(), Retry(self.dead_letter))

    async def dead_letter(self, message: BrokerMessage, error: BaseException) -> None:
        self.dead_letters.append((message, error))

    async def kick(self, message: BrokerMessage) -> None:
        await self.queue.put(message)

    async def _ack(self, task_id: str) -> None:
        self.acked.append(task_id)
        self.ack_seen.set()

    async def wait_acked(self, count: int) -> None:
        async with asyncio.timeout(2):
            while len(self.acked) < count:
                self.ack_seen.clear()
                await self.ack_seen.wait()

    async def listen(self) -> AsyncGenerator[AckableMessage]:
        while True:
            message = await self.queue.get()
            yield AckableMessage(data=message.message, ack=functools.partial(self._ack, message.task_id))


@pytest.fixture
def queue_broker() -> QueueBroker:
    return QueueBroker()

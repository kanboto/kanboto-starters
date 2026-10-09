"""The broker: NATS JetStream, consumed by pull with explicit acknowledgements, so a task is never lost.

One stream (`NATS_STREAM`) holds two subjects. Tasks are published on `NATS_SUBJECT` and read by a durable
consumer (`NATS_CONSUMER`) that every instance shares: each task goes to one instance. The stream is a work
queue, so an acknowledged task is removed from it. A task not acknowledged in time (its instance died) is
delivered again. A task that failed every attempt, an invalid message and a message the worker cannot run
(unreadable, unknown task) are published on `NATS_DEAD_LETTER_SUBJECT`, which no consumer reads: they stay
in the stream until someone inspects them.
"""

import logging

from nats.js.api import AckPolicy, ConsumerConfig, RetentionPolicy, StreamConfig
from taskiq import BrokerMessage
from taskiq_nats import PullBasedJetStreamBroker

from app.config import get_settings
from app.middleware import Observe, Retry, describe

log = logging.getLogger("app.broker")
# Beyond the task timeout, time left to publish a retry and acknowledge before JetStream redelivers.
ACK_MARGIN_S = 30
# A pull request expires and is renewed this often, so one lost by a NATS restart is never waited on for long.
FETCH_TIMEOUT_S = 5


def create() -> PullBasedJetStreamBroker:
    settings = get_settings()

    async def on_error(exc: Exception) -> None:
        log.warning("nats error", extra={"error": repr(exc)})

    async def on_disconnected() -> None:
        if not broker.client.is_closed:  # an outage, not a deliberate close
            log.warning("nats disconnected, reconnecting")

    async def on_reconnected() -> None:
        log.info("nats reconnected")

    broker = PullBasedJetStreamBroker(
        servers=[url.strip() for url in settings.nats_url.split(",")],
        subject=settings.nats_subject,
        stream_name=settings.nats_stream,
        durable=settings.nats_consumer,
        stream_config=StreamConfig(
            name=settings.nats_stream,
            subjects=[settings.nats_subject, settings.nats_dead_letter_subject],
            retention=RetentionPolicy.WORK_QUEUE,
        ),
        consumer_config=ConsumerConfig(
            durable_name=settings.nats_consumer,
            filter_subject=settings.nats_subject,
            ack_policy=AckPolicy.EXPLICIT,
            ack_wait=settings.task_timeout_s + ACK_MARGIN_S,
        ),
        pull_consume_timeout=FETCH_TIMEOUT_S,
        # Connection: waits for NATS as long as it takes, at startup and after an outage.
        name="starter-taskiq",
        connect_timeout=settings.nats_connect_timeout_s,
        max_reconnect_attempts=-1,
        error_cb=on_error,
        disconnected_cb=on_disconnected,
        reconnected_cb=on_reconnected,
    )

    async def dead_letter(message: BrokerMessage, error: BaseException) -> None:
        headers = {key: str(value) for key, value in message.labels.items()}
        headers["error"] = describe(error)
        await broker.js.publish(settings.nats_dead_letter_subject, payload=message.message, headers=headers)

    broker.add_middlewares(Observe(), Retry(dead_letter))
    return broker


broker = create()

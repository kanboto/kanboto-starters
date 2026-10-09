"""Tasks: `process_item` is an example, replace it with your domain's, keeping its conventions.

A task's arguments travel as JSON and come back as Python objects: a Pydantic model passed to `kiq` is
dumped to JSON, and the worker validates it back into the model. A task can run more than once (a retry, or
a redelivery after an instance stopped mid-task): make it idempotent. Give it an explicit `task_name`,
stable across refactors, since queued messages refer to it.
"""

import logging

from pydantic import BaseModel, ConfigDict, Field

from app import metrics
from app.broker import broker

log = logging.getLogger("app.tasks")


class Item(BaseModel):
    """The JSON body of a `process_item` task: `{"id": …, "name": …, "quantity": …, "tags": […]}`."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1)
    tags: list[str] = []


@broker.task(task_name="process_item")
async def process_item(item: Item) -> None:
    # TaskIQ only warns when an argument does not match its annotation, and passes the raw JSON on: validate
    # here, so that an invalid message fails (and is dead-lettered) instead of half-running.
    item = Item.model_validate(item)
    metrics.ITEMS_PROCESSED.inc()
    log.info("item processed", extra={"item_id": item.id, "quantity": item.quantity})

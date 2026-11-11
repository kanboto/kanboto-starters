"""Example task: replace its body with the task's work, through the business code of `common/`.

`run()` takes no argument and returns nothing; it raises on failure. It may run again after a failure, or
twice in a row: write it so that a second run does no harm (idempotent)."""

import logging

log = logging.getLogger(__name__)


async def run() -> None:
    log.info("example task done")

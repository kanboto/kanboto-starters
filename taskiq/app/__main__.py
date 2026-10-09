"""Image entrypoint: `worker` (default) runs the worker, `enqueue` sends a task."""

import argparse
import asyncio
import json
import logging.config
import sys
from typing import Any

from app import logs
from app.config import get_settings

log = logging.getLogger("app")


def worker() -> None:
    from app.worker import run

    logging.config.dictConfig(logs.config(get_settings().log_level))
    try:
        asyncio.run(run())
    except Exception:
        log.exception("worker failed")
        sys.exit(1)


async def _enqueue(name: str, kwargs: dict[str, Any]) -> str:
    from app import tasks  # noqa: F401  registers the tasks on the broker
    from app.broker import broker

    task = broker.find_task(name)
    if task is None:
        raise SystemExit(f"unknown task {name!r}, known tasks: {', '.join(broker.get_all_tasks())}")
    # Unlike the worker, a one-off command gives up when NATS stays unreachable (a few connection attempts).
    async with asyncio.timeout(get_settings().nats_connect_timeout_s * 3):
        await broker.startup()
    try:
        sent = await task.kiq(**kwargs)
    finally:
        await broker.shutdown()
    return sent.task_id


def enqueue(name: str, kwargs: str) -> None:
    """Sends one task, its keyword arguments as a JSON object, e.g.
    `enqueue process_item '{"item": {"id": "42", "name": "Widget", "quantity": 2}}'`. For trying the worker
    out and for operations; services send tasks from their own code."""
    logging.config.dictConfig(logs.config(get_settings().log_level))
    task_id = asyncio.run(_enqueue(name, json.loads(kwargs)))
    log.info("task enqueued", extra={"task": name, "task_id": task_id})


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("worker", help="run the worker (default)")
    send = commands.add_parser("enqueue", help="send one task")
    send.add_argument("task", help="task name, e.g. process_item")
    send.add_argument("kwargs", nargs="?", default="{}", help="keyword arguments, as a JSON object")
    args = parser.parse_args()
    if args.command == "enqueue":
        enqueue(args.task, args.kwargs)
    else:
        worker()


if __name__ == "__main__":
    main()

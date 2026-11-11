"""Image entrypoint: `<name>` runs the scheduled task `jobs/<name>.py`, `migrate` applies the database
migrations."""

import argparse
import asyncio
import logging.config
import sys

from common import config as common_config
from common import logs

from . import runner


def migrate() -> None:
    """Idempotent: applies pending migrations only. Run before starting a new version, never at startup."""
    from common import schema

    schema.migrate()


def main() -> None:
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}")
    parser.add_argument("task", help="the task to run, `jobs/<task>.py`, or `migrate`")
    args = parser.parse_args()
    logging.config.dictConfig(logs.config(common_config.get_settings().log_level))
    if args.task == "migrate":
        migrate()
        return
    sys.exit(asyncio.run(runner.run(args.task)))


if __name__ == "__main__":
    main()

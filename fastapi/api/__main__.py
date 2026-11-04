"""Image entrypoint: `serve` (default), `migrate`, `cleanup` (periodic), `openapi` (spec)."""

import argparse
import asyncio
import logging.config
import signal
import sys
import threading
from types import FrameType

import uvicorn

from common import config as common_config
from common import logs

from . import health
from .config import get_settings

log = logging.getLogger(__package__)


class Server(uvicorn.Server):
    """Graceful shutdown in two phases.

    On SIGTERM, `/readyz` fails at once while traffic is still served for `DRAIN_DELAY_S`, so that load
    balancers stop sending new requests. Uvicorn then stops accepting connections and lets in-flight
    requests finish within `SHUTDOWN_TIMEOUT_S`. A second signal, or SIGINT (Ctrl-C), stops right away.
    """

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        if sig != signal.SIGTERM or health.State.stopping:
            return super().handle_exit(sig, frame)
        health.State.stopping = True
        delay = get_settings().drain_delay_s
        log.info("draining", extra={"delay_s": delay})
        threading.Timer(delay, super().handle_exit, (sig, frame)).start()


def serve() -> None:
    settings = get_settings()
    log_config = logs.config(common_config.get_settings().log_level)
    logging.config.dictConfig(log_config)
    config = uvicorn.Config(
        f"{__package__}.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.port,
        log_config=log_config,
        access_log=False,  # one structured line per request is written by the application
        timeout_graceful_shutdown=settings.shutdown_timeout_s,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        server_header=False,
    )
    Server(config).run()


def migrate() -> None:
    """Idempotent: applies pending migrations only. Run before starting a new version, never at startup."""
    from common import schema

    logging.config.dictConfig(logs.config(common_config.get_settings().log_level))
    schema.migrate()


def cleanup() -> None:
    """Deletes expired idempotency keys. Run periodically, not on the request path."""
    from common import db

    from . import idempotency

    logging.config.dictConfig(logs.config(common_config.get_settings().log_level))
    db.require("cleanup")
    deleted = asyncio.run(idempotency.purge())
    log.info("idempotency keys purged", extra={"deleted": deleted})


def openapi() -> None:
    import yaml

    from .main import create_app

    yaml.safe_dump(create_app().openapi(), sys.stdout, sort_keys=False, allow_unicode=True)


COMMANDS = {"serve": serve, "migrate": migrate, "cleanup": cleanup, "openapi": openapi}


def main() -> None:
    parser = argparse.ArgumentParser(prog=f"python -m {__package__}")
    parser.add_argument("command", nargs="?", default="serve", choices=list(COMMANDS))
    COMMANDS[parser.parse_args().command]()


if __name__ == "__main__":
    main()

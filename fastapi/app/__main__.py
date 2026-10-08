"""Point d'entrée de l'image : `serve` (défaut), `migrate` (Job de migration), `openapi` (spec publique)."""

import argparse
import logging.config
import sys

import uvicorn

from app import logs
from app.config import get_settings


def serve() -> None:
    settings = get_settings()
    log_config = logs.config(settings.log_level)
    logging.config.dictConfig(log_config)
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.port,
        log_config=log_config,
        timeout_graceful_shutdown=settings.shutdown_timeout_s,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


def migrate() -> None:
    """Idempotent : n'applique que les migrations manquantes. Lancé par un Job, jamais au démarrage."""
    from alembic import command
    from alembic.config import Config

    logging.config.dictConfig(logs.config(get_settings().log_level))
    command.upgrade(Config("alembic.ini"), "head")


def openapi() -> None:
    import yaml

    from app.main import create_app

    yaml.safe_dump(create_app().openapi(), sys.stdout, sort_keys=False, allow_unicode=True)


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app")
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "migrate", "openapi"])
    {"serve": serve, "migrate": migrate, "openapi": openapi}[parser.parse_args().command]()


if __name__ == "__main__":
    main()

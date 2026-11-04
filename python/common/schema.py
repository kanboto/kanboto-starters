"""Schema migrations (`migrations/`), applied by the `migrate` command of any component: idempotent, one run
at a time, before a new version starts, never at startup."""

from alembic import command
from alembic.config import Config

from common import db


def migrate() -> None:
    """Exits with code 1, and a clear log line, when no database is configured."""
    db.require("migrate")
    command.upgrade(Config("alembic.ini"), "head")

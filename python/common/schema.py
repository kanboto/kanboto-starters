"""Schema migrations (`migrations/`), applied by the `migrate` command of any component: idempotent, one run
at a time, before a new version starts, never at startup."""

from alembic import command
from alembic.config import Config


def migrate() -> None:
    command.upgrade(Config("alembic.ini"), "head")

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from common import config, db


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[None]:
    """A fresh database, built by the migrations, so they are tested on every run.

    PostgreSQL when `TEST_DATABASE_URL` is set (as in CI and production), SQLite otherwise.
    """
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)  # plain URL from the CI service
    os.environ["DATABASE_URL"] = url
    for cached in (config.get_settings, db.engine, db.read_engine, db.sessionmaker, db.read_sessionmaker):
        cached.cache_clear()
    # `migrations/env.py` runs its own event loop: keep it out of the test's.
    alembic = Config("alembic.ini")
    if not url.startswith("sqlite"):
        await asyncio.to_thread(command.downgrade, alembic, "base")
    await asyncio.to_thread(command.upgrade, alembic, "head")
    yield
    await db.dispose()

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from common import config, db


def _clear_caches() -> None:
    for cached in (config.get_settings, db.engine, db.read_engine, db.sessionmaker, db.read_sessionmaker):
        cached.cache_clear()


@pytest.fixture
async def database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """A fresh database, built by the migrations, so they are tested on every run.

    PostgreSQL when `TEST_DATABASE_URL` is set (as in CI and production), SQLite otherwise.
    """
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)  # plain URL from the CI service
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("DATABASE_READ_URL", "")
    _clear_caches()
    # `migrations/env.py` runs its own event loop: keep it out of the test's.
    alembic = Config("alembic.ini")
    if not url.startswith("sqlite"):
        await asyncio.to_thread(command.downgrade, alembic, "base")
    await asyncio.to_thread(command.upgrade, alembic, "head")
    yield
    await db.dispose()
    _clear_caches()


@pytest.fixture
def no_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """No database configured, whatever the environment or `.env` say."""
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("DATABASE_READ_URL", "")
    _clear_caches()
    yield
    _clear_caches()

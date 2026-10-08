import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from app import db
from app.config import get_settings


@pytest.fixture(autouse=True)
async def database(tmp_path: Path) -> AsyncIterator[None]:
    """A fresh database per test, built by the migrations, so they are tested on every run.

    PostgreSQL when `TEST_DATABASE_URL` is set (as in CI and production), SQLite otherwise.
    """
    url = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    os.environ["DATABASE_URL"] = url
    for cached in (get_settings, db.engine, db.sessionmaker):
        cached.cache_clear()
    # `migrations/env.py` runs its own event loop: keep it out of the test's.
    config = Config("alembic.ini")
    if not url.startswith("sqlite"):
        await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, "head")
    yield
    await db.engine().dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c

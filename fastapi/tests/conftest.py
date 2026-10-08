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
    """A fresh SQLite database per test, built by the migrations, so they are tested on every run."""
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    for cached in (get_settings, db.engine, db.sessionmaker):
        cached.cache_clear()
    # `migrations/env.py` runs its own event loop: keep it out of the test's.
    await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
    yield
    await db.engine().dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c

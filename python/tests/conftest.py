import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from common import config, db, storage


def _clear_caches() -> None:
    for cached in (
        config.get_settings,
        db.engine,
        db.read_engine,
        db.sessionmaker,
        db.read_sessionmaker,
        storage.bucket,
    ):
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


@pytest.fixture
def buckets(monkeypatch: pytest.MonkeyPatch) -> Iterator[bool]:
    """Both buckets on the S3 server of `TEST_S3_ENDPOINT` (and `TEST_S3_ACCESS_KEY_ID`,
    `TEST_S3_SECRET_ACCESS_KEY`, `TEST_S3_BUCKET`), or none: yields whether they are reachable."""
    endpoint = os.environ.get("TEST_S3_ENDPOINT")
    for access in ("PRIVATE", "PUBLIC"):
        monkeypatch.setenv(f"S3_{access}_BUCKET", os.environ.get("TEST_S3_BUCKET", "") if endpoint else "")
        monkeypatch.setenv(f"S3_{access}_ACCESS_KEY_ID", os.environ.get("TEST_S3_ACCESS_KEY_ID", ""))
        monkeypatch.setenv(f"S3_{access}_SECRET_ACCESS_KEY", os.environ.get("TEST_S3_SECRET_ACCESS_KEY", ""))
    monkeypatch.setenv("S3_ENDPOINT", endpoint or "http://localhost:3900")
    monkeypatch.setenv("S3_PUBLIC_URL", "https://assets.example.test")
    _clear_caches()
    yield bool(endpoint)
    _clear_caches()

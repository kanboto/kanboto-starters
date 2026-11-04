"""Database: the only state of the components, which keep nothing in memory between requests or tasks.

Models live in `common/models/`, on `Base`. An API takes its sessions through the dependencies of its
`deps.py`; any other code opens one from `sessionmaker()` or `read_sessionmaker()`. The database is optional:
without `DATABASE_URL`, `engines()` is empty and opening a session raises `NotConfiguredError`.
"""

import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import DateTime, Dialect, TypeDecorator, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session

from common.config import get_settings

log = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC)


class UtcDateTime(TypeDecorator[datetime]):
    """Always an aware UTC datetime, whatever the database returns (SQLite drops the time zone)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


def _engine(url: str, *, read_only: bool) -> AsyncEngine:
    """One engine per process and role, holding a pool of open connections: a request borrows one for its
    transaction and gives it back, it never opens its own. Connections and statements are bounded by timeouts,
    so a stalled database fails requests fast instead of piling them up. A replica's engine refuses writes at
    the database level."""
    settings = get_settings()
    if url.startswith("sqlite"):  # tests
        engine = create_async_engine(url)
        if read_only:
            event.listen(
                engine.sync_engine, "connect", lambda conn, _: conn.execute("PRAGMA query_only = ON")
            )
        return engine
    # Enforced by the server too: a statement over the timeout is cancelled, not just abandoned by the client.
    server_settings = {"statement_timeout": str(int(settings.db_statement_timeout_s * 1000))}
    if read_only:
        server_settings["default_transaction_read_only"] = "on"
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_s,
        pool_recycle=settings.db_pool_recycle_s,
        connect_args={
            "timeout": settings.db_connect_timeout_s,
            # The server cancels first (statement_timeout); the client gives up one second later at most.
            "command_timeout": settings.db_statement_timeout_s + 1,
            "server_settings": server_settings,
        },
    )


class NotConfiguredError(RuntimeError):
    pass


def configured() -> bool:
    return get_settings().database_url is not None


def require(command: str) -> None:
    """Stops a command that needs the database when none is configured: a clear log line, exit code 1."""
    if not configured():
        log.error("DATABASE_URL is not set: %s needs a database", command)
        sys.exit(1)


@lru_cache
def engine() -> AsyncEngine:
    """Primary database, for writes. Created on first use: the service starts even when the database is
    down (`/readyz` reports it)."""
    url = get_settings().database_url
    if url is None:
        raise NotConfiguredError("DATABASE_URL is not set")
    return _engine(url, read_only=False)


@lru_cache
def read_engine() -> AsyncEngine:
    """Read replica (`DATABASE_READ_URL`), read-only. Without a replica, the primary's engine and pool: no
    second pool for the same database."""
    url = get_settings().database_read_url
    return _engine(url, read_only=True) if url else engine()


def engines() -> list[AsyncEngine]:
    """The pools of the configured databases; none without `DATABASE_URL`."""
    return list(dict.fromkeys([engine(), read_engine()])) if configured() else []


async def ping(timeout_s: float) -> None:
    """Raises unless every configured database answers within `timeout_s`; nothing to check without one."""
    async with asyncio.timeout(timeout_s):
        for pool in engines():
            async with pool.connect() as connection:
                await connection.execute(text("SELECT 1"))


async def dispose() -> None:
    """Closes the pools opened so far, at shutdown; a component that never used the database opens none."""
    pools = [cached() for cached in (engine, read_engine) if cached.cache_info().currsize]
    for pool in dict.fromkeys(pools):
        await pool.dispose()


class ReadOnlyError(RuntimeError):
    pass


class _ReadOnlySession(Session):
    """Session of `ReadSession`: every transaction is read-only, even on the primary's pool."""


@event.listens_for(_ReadOnlySession, "after_begin")
def _read_only_transaction(session: Session, transaction: Any, connection: Connection) -> None:
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")


@event.listens_for(_ReadOnlySession, "before_flush")
def _refuse_writes(session: Session, context: Any, instances: Any) -> None:
    raise ReadOnlyError("ReadSession is read-only: write through WriteSession")


@lru_cache
def sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine(), expire_on_commit=False)


@lru_cache
def read_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(read_engine(), expire_on_commit=False, sync_session_class=_ReadOnlySession)


async def write_session() -> AsyncIterator[AsyncSession]:
    async with sessionmaker()() as s:
        yield s


async def read_session() -> AsyncIterator[AsyncSession]:
    async with read_sessionmaker()() as s:
        yield s

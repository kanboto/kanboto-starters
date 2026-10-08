"""Database: the only state of the service, which keeps nothing in memory between requests."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import DateTime, Dialect, Integer, String, Text, TypeDecorator, Uuid, event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.config import get_settings


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


class Item(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, index=True)


class IdempotencyKey(Base):
    """Response to a creation, stored with the client's key: a retry replays it."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, index=True)


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
    server_settings = {"default_transaction_read_only": "on"} if read_only else {}
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_s,
        pool_recycle=settings.db_pool_recycle_s,
        connect_args={
            "timeout": settings.db_connect_timeout_s,
            "command_timeout": settings.db_statement_timeout_s,
            "server_settings": server_settings,
        },
    )


@lru_cache
def engine() -> AsyncEngine:
    """Primary database, for writes. Created on first use: the service starts even when the database is
    down (`/readyz` reports it)."""
    return _engine(get_settings().database_url, read_only=False)


@lru_cache
def read_engine() -> AsyncEngine:
    """Read replica (`DATABASE_READ_URL`), read-only. Without a replica, the primary's engine and pool: no
    second pool for the same database."""
    url = get_settings().database_read_url
    return _engine(url, read_only=True) if url else engine()


def engines() -> list[AsyncEngine]:
    return list(dict.fromkeys([engine(), read_engine()]))


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


# A handler that only reads uses `ReadSession`; a handler that writes uses `WriteSession` for all its work,
# including the reads it needs to decide. A write returns the updated resource, so clients need not read
# it back from a replica that may lag slightly behind.
WriteSession = Annotated[AsyncSession, Depends(write_session)]
ReadSession = Annotated[AsyncSession, Depends(read_session)]

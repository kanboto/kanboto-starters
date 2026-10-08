"""Database: the only state of the service, which keeps nothing in memory between requests."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Dialect, Integer, String, Text, TypeDecorator, Uuid
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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


@lru_cache
def engine() -> AsyncEngine:
    """Created on first use: the service starts even when the database is down (`/readyz` reports it).

    One engine per process, holding a pool of open connections: a request borrows one for its transaction and
    gives it back, it never opens its own. Connections and statements are bounded by timeouts, so a stalled
    database fails requests fast instead of piling them up.
    """
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):  # tests
        return create_async_engine(settings.database_url)
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_s,
        pool_recycle=settings.db_pool_recycle_s,
        connect_args={
            "timeout": settings.db_connect_timeout_s,
            "command_timeout": settings.db_statement_timeout_s,
        },
    )


@lru_cache
def sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine(), expire_on_commit=False)


async def session() -> AsyncIterator[AsyncSession]:
    async with sessionmaker()() as s:
        yield s

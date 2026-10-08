"""Migrations read the database URL from the environment (`DATABASE_URL`), like the application."""

import asyncio

from alembic import context
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.db import Base

# Two `migrate` runs started at once take turns on this lock instead of racing; it is released with the
# transaction.
LOCK_ID = 7_301_201


def run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": LOCK_ID})
        context.run_migrations()


async def online() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(run)
    await engine.dispose()


asyncio.run(online())

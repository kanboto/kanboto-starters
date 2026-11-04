"""Database plumbing: read-only sessions, UTC dates, the example service."""

from datetime import UTC

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from common import db
from common.models import Item
from common.services import items

pytestmark = pytest.mark.usefixtures("database")


async def test_read_session_refuses_writes() -> None:
    assert db.read_engine() is db.engine(), "no replica: one pool"
    async with db.read_sessionmaker()() as session:
        session.add(Item(name="forbidden"))
        with pytest.raises(db.ReadOnlyError):
            await session.commit()
    if db.engine().dialect.name == "postgresql":  # raw SQL too, refused by the database
        async with db.read_sessionmaker()() as session:
            with pytest.raises(DBAPIError):
                await session.execute(
                    text("INSERT INTO items (id, name, created_at) VALUES (gen_random_uuid(), 'x', now())")
                )


async def test_service_pages_in_creation_order_with_utc_dates() -> None:
    async with db.sessionmaker()() as session:
        created = [await items.create(session, f"item {i}") for i in range(3)]
        await session.commit()
    async with db.read_sessionmaker()() as session:
        first = await items.list_after(session, 2, None)
        rest = await items.list_after(session, 2, (first[-1].created_at, first[-1].id))
        fetched = await items.get(session, created[0].id)
    assert [i.id for i in first + rest] == [i.id for i in created]
    assert fetched is not None and fetched.created_at.tzinfo is UTC

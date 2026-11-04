"""Example service, over the example model: replace it with your domain's, keeping its conventions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db import utcnow
from common.models import Item


async def list_after(session: AsyncSession, limit: int, after: tuple[datetime, UUID] | None) -> list[Item]:
    """Up to `limit` items in creation order, after the position `after` (creation date, id) when given."""
    query = select(Item).order_by(Item.created_at, Item.id).limit(limit)
    if after:
        created_at, id = after
        query = query.where(
            or_(Item.created_at > created_at, and_(Item.created_at == created_at, Item.id > id))
        )
    return list(await session.scalars(query))


async def get(session: AsyncSession, item_id: UUID) -> Item | None:
    return await session.get(Item, item_id)


async def create(session: AsyncSession, name: str) -> Item:
    """Adds the item to the session's transaction; the caller commits."""
    item = Item(name=name, created_at=utcnow())
    session.add(item)
    await session.flush()
    return item

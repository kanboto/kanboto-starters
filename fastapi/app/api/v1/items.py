"""Example resource showing the API conventions: replace it with your domain's resources."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import db, idempotency, metrics, pagination
from app.errors import RESPONSES

router = APIRouter(prefix="/items", tags=["items"], responses=RESPONSES)
Session = Annotated[AsyncSession, Depends(db.session)]


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ItemOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime  # ISO 8601, UTC


def _out(item: db.Item) -> ItemOut:
    return ItemOut(id=item.id, name=item.name, created_at=item.created_at)


@router.get("", response_model=pagination.Page[ItemOut])
async def list_items(
    session: Session, limit: pagination.Limit = 20, cursor: pagination.Cursor = None
) -> pagination.Page[ItemOut]:
    query = select(db.Item).order_by(db.Item.created_at, db.Item.id).limit(limit + 1)
    if cursor:
        created_at, id = pagination.decode(cursor)
        query = query.where(
            or_(db.Item.created_at > created_at, and_(db.Item.created_at == created_at, db.Item.id > id))
        )
    rows = list(await session.scalars(query))
    page, more = rows[:limit], len(rows) > limit
    next_cursor = pagination.encode(page[-1].created_at, page[-1].id) if more else None
    return pagination.Page(items=[_out(i) for i in page], next_cursor=next_cursor)


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: UUID, session: Session) -> ItemOut:
    item = await session.get(db.Item, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    return _out(item)


@router.post("", status_code=201, response_model=ItemOut)
async def create_item(body: ItemIn, key: idempotency.KeyHeader, session: Session) -> JSONResponse:
    async def create() -> tuple[int, object]:
        item = db.Item(name=body.name, created_at=db.utcnow())
        session.add(item)
        await session.flush()
        metrics.ITEMS_CREATED.inc()
        return 201, _out(item).model_dump(mode="json")

    return await idempotency.run(session, key, body.model_dump(), create)

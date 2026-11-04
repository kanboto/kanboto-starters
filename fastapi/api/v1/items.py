"""Example resource showing the API conventions: replace it with your domain's resources. The business rules
are in `common.services`; the handlers only translate HTTP."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from common.models import Item
from common.services import items as service

from .. import deps, idempotency, metrics, pagination
from ..errors import RESPONSES

router = APIRouter(prefix="/items", tags=["items"], responses=RESPONSES)


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ItemOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime  # ISO 8601, UTC


def _out(item: Item) -> ItemOut:
    return ItemOut(id=item.id, name=item.name, created_at=item.created_at)


@router.get("", response_model=pagination.Page[ItemOut])
async def list_items(
    session: deps.ReadSession, limit: pagination.Limit = 20, cursor: pagination.Cursor = None
) -> pagination.Page[ItemOut]:
    after = pagination.decode(cursor) if cursor else None
    rows = await service.list_after(session, limit + 1, after)
    page, more = rows[:limit], len(rows) > limit
    next_cursor = pagination.encode(page[-1].created_at, page[-1].id) if more else None
    return pagination.Page(items=[_out(i) for i in page], next_cursor=next_cursor)


@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: UUID, session: deps.ReadSession) -> ItemOut:
    item = await service.get(session, item_id)
    if item is None:
        raise HTTPException(404, "item not found")
    return _out(item)


@router.post("", status_code=201, response_model=ItemOut)
async def create_item(body: ItemIn, key: idempotency.KeyHeader, session: deps.WriteSession) -> JSONResponse:
    async def create() -> tuple[int, object]:
        item = await service.create(session, body.name)
        metrics.ITEMS_CREATED.inc()
        return 201, _out(item).model_dump(mode="json")

    return await idempotency.run(session, key, body.model_dump(), create)

"""Cursor pagination, identical across the API: `?limit=&cursor=`, returns `items` and `next_cursor`.

The cursor is opaque to clients: it encodes the position (creation date, id) of the last item returned.
"""

import base64
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException, Query
from pydantic import BaseModel

Limit = Annotated[int, Query(ge=1, le=100, description="Items per page")]
Cursor = Annotated[str | None, Query(description="`next_cursor` from the previous page")]


class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None


def encode(created_at: datetime, id: UUID) -> str:
    raw = json.dumps([created_at.isoformat(), str(id)]).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode(cursor: str) -> tuple[datetime, UUID]:
    try:
        created_at, id = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        return datetime.fromisoformat(created_at), UUID(id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, "invalid cursor") from exc

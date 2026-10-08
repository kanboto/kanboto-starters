"""Pagination par curseur, de même forme sur toute l'API : `?limit=&cursor=`, rend `items` et `next_cursor`.

Le curseur est opaque pour le client : la position (date de création, identifiant) du dernier élément rendu.
"""

import base64
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException, Query
from pydantic import BaseModel

Limit = Annotated[int, Query(ge=1, le=100, description="Nombre d'éléments par page")]
Cursor = Annotated[str | None, Query(description="`next_cursor` de la page précédente")]


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
        raise HTTPException(400, "curseur invalide") from exc

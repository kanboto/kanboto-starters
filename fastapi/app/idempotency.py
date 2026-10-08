"""`Idempotency-Key` sur les créations : une nouvelle tentative avec la même clé rejoue la même réponse.

La clé et la réponse sont gardées en base (`IDEMPOTENCY_TTL_S`) : n'importe quel réplica peut rejouer.
Même clé avec un autre corps → 422. Deux requêtes simultanées avec la même clé : la contrainte d'unicité
tranche, la seconde rejoue la réponse de la première.
"""

import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Annotated, Any

from fastapi import Header
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import IdempotencyKey, utcnow
from app.errors import problem

KeyHeader = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=200,
        description="Clé unique par opération, générée par le client (un UUID) et renvoyée à l'identique "
        "à chaque nouvelle tentative.",
    ),
]


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


async def run(
    session: AsyncSession,
    key: str,
    payload: Any,
    create: Callable[[], Awaitable[tuple[int, Any]]],
) -> JSONResponse:
    """`create` fait l'opération et rend (statut, corps) ; elle n'est lancée qu'une fois par clé."""
    expiry = utcnow() - timedelta(seconds=get_settings().idempotency_ttl_s)
    await session.execute(delete(IdempotencyKey).where(IdempotencyKey.created_at < expiry))
    request_hash = _hash(payload)
    stored = await session.scalar(select(IdempotencyKey).where(IdempotencyKey.key == key))
    if stored is None:
        status, body = await create()
        stored_body = json.dumps(body)
        session.add(IdempotencyKey(key=key, request_hash=request_hash, status_code=status, body=stored_body))
        try:
            await session.commit()
            return JSONResponse(body, status_code=status)
        except IntegrityError:
            await session.rollback()
            stored = await session.scalar(select(IdempotencyKey).where(IdempotencyKey.key == key))
            if stored is None:
                raise
    if stored.request_hash != request_hash:
        return problem(422, "cette clé d'idempotence a déjà servi pour une autre requête")
    replayed = {"Idempotent-Replayed": "true"}
    return JSONResponse(json.loads(stored.body), status_code=stored.status_code, headers=replayed)

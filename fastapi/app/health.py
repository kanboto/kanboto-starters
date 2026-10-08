"""Sondes de Kubernetes et métriques, à la racine : jamais exposées par l'ingress.

`/healthz` (liveness) répond tant que le serveur répond ; `/readyz` (readiness) vérifie les dépendances et
passe à 503 dès que l'arrêt commence, pour que Kubernetes retire le pod avant qu'il ne s'arrête.
"""

import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app import db, metrics

log = logging.getLogger(__name__)
router = APIRouter(include_in_schema=False)


class State:
    stopping = False


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, str]:
    if State.stopping:
        response.status_code = 503
        return {"status": "stopping"}
    try:
        async with db.engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # toute panne de la base rend le pod indisponible, sans le tuer
        log.warning("base injoignable", extra={"error": str(exc)})
        response.status_code = 503
        return {"status": "unavailable"}
    return {"status": "ok"}


@router.get("/metrics")
async def prometheus() -> Response:
    return metrics.exposition()

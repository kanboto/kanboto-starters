"""Kubernetes probes and metrics, at the root path, outside `/api` and `/internal`.

`/healthz` (liveness) answers as long as the server does; `/readyz` (readiness) checks dependencies and
returns 503 as soon as shutdown starts, so Kubernetes stops routing traffic before the pod exits.
"""

import asyncio
import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app import db, metrics
from app.config import get_settings

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
        async with asyncio.timeout(get_settings().ready_timeout_s), db.engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # a database outage makes the pod unready, it does not kill it
        log.warning("database unreachable", extra={"error": str(exc)})
        response.status_code = 503
        return {"status": "unavailable"}
    return {"status": "ok"}


@router.get("/metrics")
async def prometheus() -> Response:
    return metrics.exposition()

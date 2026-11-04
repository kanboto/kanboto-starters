"""Liveness and readiness probes and metrics, at the root path, outside `/api` and `/internal`.

`/healthz` (liveness) answers as long as the server does; `/readyz` (readiness) checks dependencies (the
database, when one is configured) and returns 503 as soon as shutdown starts, so traffic is routed elsewhere
before the process exits.
"""

import logging

from fastapi import APIRouter, Response

from common import config as common_config
from common import db

from . import metrics

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
        await db.ping(common_config.get_settings().ready_timeout_s)
    except Exception as exc:  # a database outage makes the instance unready, it does not kill it
        log.warning("database unreachable", extra={"error": str(exc)})
        response.status_code = 503
        return {"status": "unavailable"}
    return {"status": "ok"}


@router.get("/metrics")
async def prometheus() -> Response:
    return metrics.exposition()

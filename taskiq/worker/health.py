"""Liveness and readiness probes and metrics, on `PORT`: the worker's only HTTP surface, a bare ASGI app.

`/healthz` (liveness) answers as long as the process does; `/readyz` (readiness) answers 200 while the worker
is connected to NATS and consuming, and the database and buckets answer when configured; 503 as soon as
shutdown starts.
"""

import json
import logging
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from common import config as common_config
from common import db, storage
from common import metrics as metrics_of_process

from . import metrics

log = logging.getLogger(__name__)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

JSON = "application/json"


class State:
    stopping = False
    # Set by the worker once the stream and consumer are set up: is the NATS connection up?
    connected: Callable[[], bool] | None = None


def _json(status: int, body: dict[str, str]) -> tuple[int, bytes, str]:
    return status, json.dumps(body).encode(), JSON


async def _healthz() -> tuple[int, bytes, str]:
    return _json(200, {"status": "ok"})


async def _readyz() -> tuple[int, bytes, str]:
    if State.stopping:
        return _json(503, {"status": "stopping"})
    if State.connected is None or not State.connected():
        return _json(503, {"status": "unavailable"})
    timeout_s = common_config.get_settings().ready_timeout_s
    try:
        await db.ping(timeout_s)
    except Exception as exc:  # a database outage makes the instance unready, it does not kill it
        log.warning("database unreachable", extra={"error": str(exc)})
        return _json(503, {"status": "unavailable"})
    try:
        await storage.ping(timeout_s)
    except Exception as exc:
        log.warning("object storage unreachable", extra={"error": str(exc)})
        return _json(503, {"status": "unavailable"})
    return _json(200, {"status": "ok"})


async def _metrics() -> tuple[int, bytes, str]:
    return 200, *metrics_of_process.exposition(metrics.REGISTRY)


ROUTES: dict[str, Callable[[], Awaitable[tuple[int, bytes, str]]]] = {
    "/healthz": _healthz,
    "/readyz": _readyz,
    "/metrics": _metrics,
}


async def _respond(method: str, path: str) -> tuple[int, bytes, str]:
    route = ROUTES.get(path)
    if route is None:
        return _json(404, {"status": "not found"})
    if method not in ("GET", "HEAD"):
        return _json(405, {"status": "method not allowed"})
    return await route()


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "http":
        return
    status, body, content_type = await _respond(scope["method"], scope["path"])
    headers = [(b"content-type", content_type.encode()), (b"content-length", str(len(body)).encode())]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if scope["method"] == "HEAD" else body})

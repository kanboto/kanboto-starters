"""Liveness and readiness probes and metrics, on `PORT`: the worker's only HTTP surface, a bare ASGI app.

`/healthz` (liveness) answers as long as the process does; `/readyz` (readiness) answers 200 while the worker
is connected to NATS and consuming, and 503 as soon as shutdown starts.
"""

import json
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from app import metrics

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


def _respond(method: str, path: str) -> tuple[int, bytes, str]:
    if path not in ("/healthz", "/readyz", "/metrics"):
        return _json(404, {"status": "not found"})
    if method not in ("GET", "HEAD"):
        return _json(405, {"status": "method not allowed"})
    if path == "/healthz":
        return _json(200, {"status": "ok"})
    if path == "/metrics":
        return 200, *metrics.exposition()
    if State.stopping:
        return _json(503, {"status": "stopping"})
    if State.connected is None or not State.connected():
        return _json(503, {"status": "unavailable"})
    return _json(200, {"status": "ok"})


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "http":
        return
    status, body, content_type = _respond(scope["method"], scope["path"])
    headers = [(b"content-type", content_type.encode()), (b"content-length", str(len(body)).encode())]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if scope["method"] == "HEAD" else body})

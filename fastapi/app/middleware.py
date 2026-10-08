"""Per-request plumbing, as plain ASGI middleware: request id, structured access log, metrics, body size
limit and security headers."""

import logging
import re
import time
import uuid
from typing import Any

from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import logs, metrics
from app.config import get_settings

log = logging.getLogger("app.access")
REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
]


class RequestMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        incoming = headers.get(b"x-request-id", b"").decode("latin-1")
        rid = incoming if REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = logs.request_id.set(rid)
        path: str = scope["path"]
        limit = get_settings().max_body_bytes
        status = 500
        start = time.perf_counter()

        declared = headers.get(b"content-length", b"")
        if declared.isdigit() and int(declared) > limit:
            receive = _refuse

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise HTTPException(413, f"request body larger than {limit} bytes")
            return message

        async def tagged_send(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                extra: list[tuple[bytes, bytes]] = [(b"x-request-id", rid.encode()), *SECURITY_HEADERS]
                if path.startswith(("/api/", "/internal/")):
                    extra.append((b"cache-control", b"no-store"))
                message["headers"] = [*message.get("headers", []), *extra]
            await send(message)

        try:
            await self.app(scope, limited_receive, tagged_send)
        finally:
            if path not in metrics.UNTRACKED:
                route = metrics.route(scope["app"], path)
                duration = time.perf_counter() - start
                metrics.observe(scope["method"], route, status, duration)
                log.info(
                    "request",
                    extra={
                        "method": scope["method"],
                        "route": route,
                        "path": path,
                        "status": status,
                        "duration_ms": round(duration * 1000, 1),
                        "client": _client(scope),
                    },
                )
            logs.request_id.reset(token)


async def _refuse() -> dict[str, Any]:
    raise HTTPException(413, f"request body larger than {get_settings().max_body_bytes} bytes")


def _client(scope: Scope) -> str | None:
    client = scope.get("client")
    return str(client[0]) if client else None

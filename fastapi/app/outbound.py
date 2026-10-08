"""Calls to other services: one HTTP client per process, created at startup, with bounded timeouts and a
connection pool. The current request id is forwarded, so logs can be followed from one service to the next.

    @router.get("/quotes/{quote_id}")
    async def quote(quote_id: str, http: outbound.Client) -> Quote:
        response = await http.get(f"{settings.billing_api_url}/api/v1/quotes/{quote_id}")
        response.raise_for_status()
        ...
"""

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app import logs
from app.config import get_settings


async def _forward_request_id(request: httpx.Request) -> None:
    if (current := logs.request_id.get()) and "x-request-id" not in request.headers:
        request.headers["X-Request-ID"] = current


def client() -> httpx.AsyncClient:
    settings = get_settings()
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout_s, connect=settings.http_connect_timeout_s),
        limits=httpx.Limits(max_connections=settings.http_max_connections),
        event_hooks={"request": [_forward_request_id]},
    )


def _client(request: Request) -> httpx.AsyncClient:
    http: httpx.AsyncClient = request.app.state.http
    return http


Client = Annotated[httpx.AsyncClient, Depends(_client)]

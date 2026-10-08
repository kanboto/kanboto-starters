"""Production hardening: request ids, access logs, body limit, security headers, deprecation, shutdown."""

import json
import logging
import signal
import time
from datetime import UTC, datetime, timedelta

import pytest
import uvicorn
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient

from app import __main__ as entry
from app import health, idempotency
from app.config import get_settings
from app.deprecation import deprecate


async def test_request_id_is_kept_or_generated(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.access")
    response = await client.get("/api/v1/items", headers={"X-Request-ID": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"
    [line] = [r for r in caplog.records if r.name == "app.access"]
    assert line.__dict__["route"] == "/api/v1/items" and line.__dict__["status"] == 200
    generated = (await client.get("/api/v1/items", headers={"X-Request-ID": "bad id!"})).headers[
        "x-request-id"
    ]
    assert generated != "bad id!" and len(generated) == 32


async def test_security_headers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/items")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store" and "server" not in response.headers


async def test_body_limit(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "max_body_bytes", 64)
    response = await client.post(
        "/api/v1/items", content=json.dumps({"name": "x" * 100}), headers={"Idempotency-Key": "k" * 16}
    )
    assert response.status_code == 413 and response.headers["content-type"] == "application/problem+json"


async def test_deprecated_router_sends_headers_and_marks_spec() -> None:
    old = APIRouter(prefix="/api/v1")

    @old.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "v1"}

    app = FastAPI()
    since, sunset = datetime(2026, 11, 1, tzinfo=UTC), datetime(2027, 5, 1, tzinfo=UTC)
    app.include_router(deprecate(old, since=since, sunset=sunset, successor="/api/v2"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        response = await c.get("/api/v1/ping")
    assert response.headers["deprecation"] == f"@{int(since.timestamp())}"
    assert response.headers["sunset"] == "Sat, 01 May 2027 00:00:00 GMT"
    assert response.headers["link"] == '</api/v2>; rel="successor-version"'
    assert app.openapi()["paths"]["/api/v1/ping"]["get"]["deprecated"] is True
    with pytest.raises(ValueError):
        deprecate(old, since=sunset, sunset=since)


async def test_expired_keys_are_purged_and_reusable(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = await client.post("/api/v1/items", json={"name": "a"}, headers={"Idempotency-Key": "key-" * 4})
    monkeypatch.setattr(idempotency, "utcnow", lambda: datetime.now(UTC) + timedelta(days=2))
    again = await client.post("/api/v1/items", json={"name": "b"}, headers={"Idempotency-Key": "key-" * 4})
    assert again.status_code == 201 and again.json()["id"] != first.json()["id"]
    assert await idempotency.purge() == 1


def test_sigterm_drains_before_stopping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "drain_delay_s", 0.05)
    server = entry.Server(uvicorn.Config("app.main:create_app", factory=True))
    server.handle_exit(signal.SIGTERM, None)
    assert health.State.stopping and not server.should_exit
    time.sleep(0.2)
    assert server.should_exit
    health.State.stopping = False


async def test_cors_only_for_configured_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.main import create_app

    monkeypatch.setattr(get_settings(), "cors_origins", "https://app.example.com")
    preflight = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "idempotency-key"}
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://t") as c:
        allowed = await c.options("/api/v1/items", headers={"Origin": "https://app.example.com", **preflight})
        other = await c.options("/api/v1/items", headers={"Origin": "https://evil.example.com", **preflight})
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"
    assert "access-control-allow-origin" not in other.headers


async def test_outbound_client_is_bounded_and_forwards_request_id() -> None:
    import httpx

    from app import logs, outbound

    seen: list[httpx.Request] = []
    http = outbound.client()
    assert http.timeout.read == get_settings().http_timeout_s and http.timeout.connect == 3

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    http._transport = httpx.MockTransport(record)
    token = logs.request_id.set("rid-42")
    try:
        await http.get("http://billing/api/v1/quotes/1")
    finally:
        logs.request_id.reset(token)
        await http.aclose()
    assert seen[0].headers["x-request-id"] == "rid-42"

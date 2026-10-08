"""Runtime contract: probes, metrics, JSON logs, RFC 9457 errors, up-to-date OpenAPI spec."""

import json
import logging
import subprocess
import sys
from pathlib import Path

from httpx import AsyncClient

from app import health, logs


async def test_probes(client: AsyncClient) -> None:
    assert (await client.get("/healthz")).json() == {"status": "ok"}
    assert (await client.get("/readyz")).status_code == 200
    health.State.stopping = True
    try:
        assert (await client.get("/readyz")).status_code == 503
    finally:
        health.State.stopping = False


async def test_metrics_use_route_templates(client: AsyncClient) -> None:
    await client.get("/api/v1/items/00000000-0000-0000-0000-000000000000")
    text = (await client.get("/metrics")).text
    assert 'http_requests_total{method="GET",route="/api/v1/items/{item_id}",status="404"} 1.0' in text
    assert "process_cpu_seconds_total" in text or "python_gc_objects_collected_total" in text


async def test_errors_are_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/items/pas-un-uuid")
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Unprocessable Content" and response.json()["errors"]


def test_logs_are_json() -> None:
    record = logging.makeLogRecord({"name": "app", "levelname": "INFO", "msg": "ready", "request_id": "r1"})
    entry = json.loads(logs.JsonFormatter().format(record))
    assert entry["message"] == "ready" and entry["level"] == "info" and entry["request_id"] == "r1"


def test_openapi_file_is_up_to_date() -> None:
    generated = subprocess.run(
        [sys.executable, "-m", "app", "openapi"], capture_output=True, text=True, check=True
    ).stdout
    hint = "run: python -m app openapi > openapi/public.yaml"
    assert generated == Path("openapi/public.yaml").read_text(), hint

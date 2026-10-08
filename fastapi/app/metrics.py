"""Prometheus metrics: runtime (process, garbage collector) and HTTP requests.

One process per container: scale out with replicas, not uvicorn workers. Counters stay accurate without
the multiprocess mode of `prometheus_client`.
"""

import re
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "route"])
# Example business metric: replace it with your domain's.
ITEMS_CREATED = Counter("items_created_total", "Items created")

UNTRACKED = {"/healthz", "/readyz", "/metrics"}


def _templates(app: FastAPI) -> list[tuple[re.Pattern[str], str]]:
    """Route templates from the spec (`/api/v1/items/{item_id}`), compiled once per application."""
    if not hasattr(app.state, "route_templates"):
        app.state.route_templates = [
            (re.compile("^" + re.sub(r"\\{[^/]+\\}", "[^/]+", re.escape(path)) + "$"), path)
            for path in app.openapi().get("paths", {})
        ]
    return list(app.state.route_templates)


def _route(request: Request) -> str:
    """The route template, never the raw path, so metric cardinality stays bounded."""
    path = request.url.path
    return next((template for regex, template in _templates(request.app) if regex.match(path)), "unknown")


async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    if request.url.path in UNTRACKED:
        return await call_next(request)
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = _route(request)
        LATENCY.labels(request.method, route).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, route, str(status)).inc()


def exposition() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

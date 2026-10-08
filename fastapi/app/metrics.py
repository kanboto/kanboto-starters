"""Métriques Prometheus : celles du runtime (processus, ramasse-miettes) et des requêtes HTTP.

Un seul processus par conteneur : on passe à l'échelle par réplicas, pas par workers uvicorn. Les compteurs
restent donc justes sans le mode multiprocessus de `prometheus_client`.
"""

import re
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter("http_requests_total", "Requêtes HTTP traitées", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Durée des requêtes HTTP", ["method", "route"])
# Exemple de métrique métier : à remplacer par celles du domaine.
ITEMS_CREATED = Counter("items_created_total", "Items créés")

UNTRACKED = {"/healthz", "/readyz", "/metrics"}


def _templates(app: FastAPI) -> list[tuple[re.Pattern[str], str]]:
    """Gabarits des routes de la spec (`/api/v1/items/{item_id}`), compilés une fois par application."""
    if not hasattr(app.state, "route_templates"):
        app.state.route_templates = [
            (re.compile("^" + re.sub(r"\\{[^/]+\\}", "[^/]+", re.escape(path)) + "$"), path)
            for path in app.openapi().get("paths", {})
        ]
    return list(app.state.route_templates)


def _route(request: Request) -> str:
    """Le gabarit de la route, jamais le chemin brut : la cardinalité des métriques reste bornée."""
    path = request.url.path
    return next((template for regex, template in _templates(request.app) if regex.match(path)), "inconnue")


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

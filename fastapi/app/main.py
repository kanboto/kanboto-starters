"""Application: public routes under `/api/v<N>`, probes and metrics at the root path."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db, errors, health, outbound
from app.api import v1
from app.config import get_settings
from app.middleware import RequestMiddleware

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("starting")
    app.state.http = outbound.client()
    yield
    # SIGTERM received: uvicorn stops accepting connections and drains in-flight ones (SHUTDOWN_TIMEOUT_S).
    health.State.stopping = True
    await app.state.http.aclose()
    for engine in db.engines():
        await engine.dispose()
    log.info("stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="starter-fastapi", version="1.0.0", lifespan=lifespan)
    errors.install(app)
    if origins := [o.strip() for o in get_settings().cors_origins.split(",") if o.strip()]:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID", "Deprecation", "Sunset", "Link", "Idempotent-Replayed"],
        )
    app.add_middleware(RequestMiddleware)
    app.include_router(health.router)
    app.include_router(v1.router)
    return app

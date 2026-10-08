"""Application: public routes under `/api/v<N>`, probes and metrics at the root path."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db, errors, health
from app.api import v1
from app.middleware import RequestMiddleware

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("starting")
    yield
    # SIGTERM received: uvicorn stops accepting connections and drains in-flight ones (SHUTDOWN_TIMEOUT_S).
    health.State.stopping = True
    await db.engine().dispose()
    log.info("stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="starter-fastapi", version="1.0.0", lifespan=lifespan)
    errors.install(app)
    app.add_middleware(RequestMiddleware)
    app.include_router(health.router)
    app.include_router(v1.router)
    return app

"""Application : routes publiques sous `/api/v<N>`, sondes et métriques à la racine."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db, errors, health, metrics
from app.api import v1

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("démarrage")
    yield
    # SIGTERM reçu : uvicorn n'accepte plus de connexion et termine celles en cours (SHUTDOWN_TIMEOUT_S).
    health.State.stopping = True
    await db.engine().dispose()
    log.info("arrêt")


def create_app() -> FastAPI:
    app = FastAPI(title="starter-fastapi", version="1.0.0", lifespan=lifespan)
    errors.install(app)
    app.middleware("http")(metrics.middleware)
    app.include_router(health.router)
    app.include_router(v1.router)
    return app

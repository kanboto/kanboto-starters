"""RFC 9457 problem details (`application/problem+json`) for every 4xx and 5xx response."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

log = logging.getLogger(__name__)
MEDIA_TYPE = "application/problem+json"


class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    errors: list[dict[str, Any]] | None = None


def problem(status: int, detail: str | None = None, **extra: Any) -> JSONResponse:
    body = Problem(title=HTTPStatus(status).phrase, status=status, detail=detail, **extra)
    return JSONResponse(body.model_dump(exclude_none=True), status_code=status, media_type=MEDIA_TYPE)


# Error responses declared on every operation, so the OpenAPI spec documents them for clients.
RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": Problem, "content": {MEDIA_TYPE: {}}} for status in (400, 404, 409, 422, 500)
}


def install(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return problem(exc.status_code, str(exc.detail) if exc.detail else None)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return problem(422, "invalid request", errors=errors)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unexpected error", extra={"path": request.url.path})
        return problem(500)

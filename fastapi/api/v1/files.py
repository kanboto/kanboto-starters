"""Example of file handling through object storage (`common.storage`): replace it with your domain's files.

The body is the file itself (no multipart), streamed to the bucket without being held in memory, up to
`MAX_UPLOAD_BYTES`. A retry with the same `Idempotency-Key` replays the first response without storing the
file again. A private file is read back through the API; a public one is loaded by the browser from
its `url`, never through the API.
"""

from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from common import storage

from .. import deps, idempotency
from ..errors import RESPONSES

router = APIRouter(prefix="/files", tags=["files"], responses=RESPONSES)


class FileOut(BaseModel):
    key: str
    url: str | None  # public files only: where the browser loads it


def _require(access: storage.Access) -> None:
    if not storage.configured(access):
        raise HTTPException(404, f"no {access} bucket")


@router.post("", status_code=201, response_model=FileOut)
async def upload_file(
    request: Request,
    key: idempotency.KeyHeader,
    session: deps.WriteSession,
    access: Literal["private", "public"] = "private",
) -> JSONResponse:
    _require(access)
    content_type = request.headers.get("content-type", "application/octet-stream")

    async def body() -> AsyncIterator[bytes]:
        async for chunk in request.stream():
            if chunk:
                yield chunk

    async def create() -> tuple[int, object]:
        stored = await storage.put(access, body(), content_type)
        url = storage.public_url(stored) if access == "public" else None
        return 201, FileOut(key=stored, url=url).model_dump(mode="json")

    return await idempotency.run(session, key, {"access": access, "content_type": content_type}, create)


@router.get("/{key}", response_class=StreamingResponse)
async def download_file(key: str) -> StreamingResponse:
    """A private file, streamed from the bucket."""
    _require("private")
    try:
        content, content_type = await storage.get("private", key)
    except FileNotFoundError:
        raise HTTPException(404, "file not found") from None
    return StreamingResponse(content, media_type=content_type)

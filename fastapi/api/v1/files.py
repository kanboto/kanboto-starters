"""Example of file handling through object storage (`common.storage`): replace it with your domain's files.

The body is the file itself (no multipart), streamed to the bucket without being held in memory, up to
`MAX_UPLOAD_BYTES`. A private file is read back through the API; a public one is loaded by the browser from
its `url`, never through the API.
"""

from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common import storage

from ..errors import RESPONSES

router = APIRouter(prefix="/files", tags=["files"], responses=RESPONSES)


class FileOut(BaseModel):
    key: str
    url: str | None  # public files only: where the browser loads it


def _require(access: storage.Access) -> None:
    if not storage.configured(access):
        raise HTTPException(404, f"no {access} bucket")


@router.post("", status_code=201, response_model=FileOut)
async def upload_file(request: Request, access: Literal["private", "public"] = "private") -> FileOut:
    _require(access)

    async def body() -> AsyncIterator[bytes]:
        async for chunk in request.stream():
            if chunk:
                yield chunk

    content_type = request.headers.get("content-type", "application/octet-stream")
    key = await storage.put(access, body(), content_type)
    return FileOut(key=key, url=storage.public_url(key) if access == "public" else None)


@router.get("/{key}", response_class=StreamingResponse)
async def download_file(key: str) -> StreamingResponse:
    """A private file, streamed from the bucket."""
    _require("private")
    try:
        content, content_type = await storage.get("private", key)
    except FileNotFoundError:
        raise HTTPException(404, "file not found") from None
    return StreamingResponse(content, media_type=content_type)

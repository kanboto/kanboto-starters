"""Object storage (S3): the files of the components, which keep none on their read-only filesystem.

Two buckets at most, each optional like the database:

- `private`: files read through the API only (users' documents), never linked to directly;
- `public`: files anyone may read at `S3_PUBLIC_URL/<key>` (catalogue images, avatars). Keys are random, so
  nothing private ever lands there.

A bucket is configured when its name is set (`S3_PRIVATE_BUCKET`, `S3_PUBLIC_BUCKET`); `bucket()` raises
`NotConfiguredError` otherwise. Every call is bounded by `S3_TIMEOUT_S`.
"""

import asyncio
import uuid
from collections.abc import AsyncIterable, AsyncIterator
from datetime import timedelta
from functools import lru_cache
from typing import Literal

import obstore
from obstore.store import S3Store

from common.config import get_settings

Access = Literal["private", "public"]
ACCESSES: tuple[Access, ...] = ("private", "public")


class NotConfiguredError(RuntimeError):
    pass


def configured(access: Access) -> bool:
    return bool(_credentials(access)[0])


def _credentials(access: Access) -> tuple[str | None, str | None, str | None]:
    s = get_settings()
    if access == "private":
        return s.s3_private_bucket, s.s3_private_access_key_id, s.s3_private_secret_access_key
    return s.s3_public_bucket, s.s3_public_access_key_id, s.s3_public_secret_access_key


@lru_cache
def bucket(access: Access) -> S3Store:
    """One client per bucket and process, reusing its connections."""
    name, key_id, secret = _credentials(access)
    if not name:
        raise NotConfiguredError(f"S3_{access.upper()}_BUCKET is not set")
    settings = get_settings()
    return S3Store(
        name,
        config={
            "endpoint": settings.s3_endpoint,
            "region": settings.s3_region,
            "access_key_id": key_id or "",
            "secret_access_key": secret or "",
            "virtual_hosted_style_request": False,
        },
        client_options={
            "allow_http": settings.s3_endpoint.startswith("http://"),
            "connect_timeout": timedelta(seconds=settings.s3_connect_timeout_s),
            "timeout": timedelta(seconds=settings.s3_timeout_s),
        },
    )


def new_key(suffix: str = "") -> str:
    """A random object key: unguessable, so a public URL reveals nothing about the others."""
    return f"{uuid.uuid4().hex}{suffix}"


def public_url(key: str) -> str:
    """Address of an object of the public bucket, as the browser loads it."""
    base = get_settings().s3_public_url
    if not base:
        raise NotConfiguredError("S3_PUBLIC_URL is not set")
    return f"{base.rstrip('/')}/{key}"


async def ping(timeout_s: float) -> None:
    """Raises unless every configured bucket answers within `timeout_s`; nothing to check without one."""
    async with asyncio.timeout(timeout_s):
        for access in ACCESSES:
            if configured(access):
                await obstore.list_with_delimiter_async(bucket(access), prefix="readyz/")


async def put(access: Access, chunks: AsyncIterable[bytes], content_type: str) -> str:
    """Streams a new object to the bucket, never holding it whole in memory; returns its random key."""
    key = new_key()
    await obstore.put_async(bucket(access), key, chunks, attributes={"Content-Type": content_type})
    return key


async def get(access: Access, key: str) -> tuple[AsyncIterator[bytes], str]:
    """The object's content, as a stream, and its type; raises `FileNotFoundError` when it does not exist."""
    found = await obstore.get_async(bucket(access), key)
    content_type = str(found.attributes.get("Content-Type") or "application/octet-stream")
    return (bytes(chunk) async for chunk in found.stream()), content_type

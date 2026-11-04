"""Files: streamed to the bucket under a random key, read back through the API when private, bounded by
`MAX_UPLOAD_BYTES`. The buckets are in memory (obstore's `MemoryStore`)."""

from collections.abc import Iterator
from functools import lru_cache

import pytest
from httpx import AsyncClient
from obstore.store import MemoryStore

from api import config
from common import config as common_config
from common import storage


@pytest.fixture
def memory_buckets(buckets: bool, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    stores = {"private": MemoryStore(), "public": MemoryStore()}
    monkeypatch.setenv("S3_PRIVATE_BUCKET", "private")
    monkeypatch.setenv("S3_PUBLIC_BUCKET", "public")
    monkeypatch.setattr(storage, "bucket", lru_cache(lambda access: stores[access]))
    common_config.get_settings.cache_clear()
    yield
    common_config.get_settings.cache_clear()


async def test_private_file_round_trip(client: AsyncClient, memory_buckets: None) -> None:
    pdf = {"Content-Type": "application/pdf"}
    created = await client.post("/api/v1/files", content=b"%PDF-1.7", headers=pdf)
    assert created.status_code == 201
    body = created.json()
    assert body["url"] is None and len(body["key"]) == 32
    read = await client.get(f"/api/v1/files/{body['key']}")
    assert (read.content, read.headers["content-type"]) == (b"%PDF-1.7", "application/pdf")
    assert (await client.get("/api/v1/files/absent")).status_code == 404


async def test_public_file_has_its_address(client: AsyncClient, memory_buckets: None) -> None:
    png = {"Content-Type": "image/png"}
    created = await client.post("/api/v1/files?access=public", content=b"png", headers=png)
    body = created.json()
    assert body["url"] == f"https://assets.example.test/{body['key']}"


async def test_upload_is_bounded(
    client: AsyncClient, memory_buckets: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "4")
    config.get_settings.cache_clear()
    response = await client.post("/api/v1/files", content=b"12345")
    assert response.status_code == 413


async def test_no_bucket_no_files(client: AsyncClient, buckets: bool) -> None:
    if buckets:
        pytest.skip("buckets configured")
    assert (await client.post("/api/v1/files", content=b"x")).status_code == 404

"""Object storage: optional per bucket, random keys, public addresses; a real round trip on the S3 server of
`TEST_S3_ENDPOINT` when set."""

import obstore
import pytest

from common import storage


async def test_buckets_are_optional(buckets: bool) -> None:
    if buckets:
        pytest.skip("buckets configured")
    assert not storage.configured("private") and not storage.configured("public")
    await storage.ping(0.1)
    with pytest.raises(storage.NotConfiguredError):
        storage.bucket("private")


def test_public_url_and_random_keys(buckets: bool) -> None:
    key = storage.new_key(".png")
    assert key.endswith(".png") and len(key) == 36 and key != storage.new_key(".png")
    assert storage.public_url(key) == f"https://assets.example.test/{key}"


async def test_round_trip(buckets: bool) -> None:
    if not buckets:
        pytest.skip("TEST_S3_ENDPOINT is not set")
    await storage.ping(5)
    key = storage.new_key()
    await obstore.put_async(storage.bucket("private"), key, b"hello")
    assert bytes(await (await obstore.get_async(storage.bucket("private"), key)).bytes_async()) == b"hello"
    await obstore.delete_async(storage.bucket("private"), key)

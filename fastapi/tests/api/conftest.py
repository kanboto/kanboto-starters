from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from api import config


@pytest.fixture(autouse=True)
def fresh_database_and_settings(database: None) -> Iterator[None]:
    """Every test of the API gets a fresh database (`tests/conftest.py`) and its own settings."""
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from api.main import create_app

    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c

"""Conventions de l'API sur la ressource d'exemple : idempotence, pagination par curseur."""

from uuid import uuid4

from httpx import AsyncClient


async def create(client: AsyncClient, name: str, key: str | None = None) -> dict[str, object]:
    headers = {"Idempotency-Key": key or str(uuid4())}
    response = await client.post("/api/v1/items", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return dict(response.json())


async def test_creation_is_idempotent(client: AsyncClient) -> None:
    key = str(uuid4())
    first = await create(client, "a", key)
    replay = await client.post("/api/v1/items", json={"name": "a"}, headers={"Idempotency-Key": key})
    assert replay.status_code == 201 and replay.json() == first
    assert replay.headers["Idempotent-Replayed"] == "true"
    other = await client.post("/api/v1/items", json={"name": "b"}, headers={"Idempotency-Key": key})
    assert other.status_code == 422
    assert len((await client.get("/api/v1/items")).json()["items"]) == 1


async def test_creation_requires_a_key(client: AsyncClient) -> None:
    response = await client.post("/api/v1/items", json={"name": "a"})
    assert response.status_code == 422 and response.headers["content-type"] == "application/problem+json"


async def test_cursor_pagination(client: AsyncClient) -> None:
    names = [str((await create(client, f"item {i}"))["name"]) for i in range(5)]
    seen: list[str] = []
    cursor = None
    while True:
        params = {"limit": "2", **({"cursor": cursor} if cursor else {})}
        page = (await client.get("/api/v1/items", params=params)).json()
        seen += [i["name"] for i in page["items"]]
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert seen == names
    assert (await client.get("/api/v1/items", params={"cursor": "%%%"})).status_code == 400

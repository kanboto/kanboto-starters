"""Deprecating an API version: every response of the router carries `Deprecation` (RFC 9745) and `Sunset`
(RFC 8594), and its operations are marked `deprecated` in the OpenAPI spec.

    since, sunset = datetime(2026, 11, 1, tzinfo=UTC), datetime(2027, 5, 1, tzinfo=UTC)
    app.include_router(deprecate(v1.router, since=since, sunset=sunset, successor="/api/v2"))

The version keeps being served until its sunset date; removing it before then is a breaking change.
"""

from datetime import UTC, datetime
from email.utils import format_datetime

from fastapi import APIRouter, Depends, Response


def headers(since: datetime, sunset: datetime, successor: str | None = None) -> dict[str, str]:
    values = {
        "Deprecation": f"@{int(since.astimezone(UTC).timestamp())}",
        "Sunset": format_datetime(sunset.astimezone(UTC), usegmt=True),
    }
    if successor:
        values["Link"] = f'<{successor}>; rel="successor-version"'
    return values


def deprecate(
    router: APIRouter, *, since: datetime, sunset: datetime, successor: str | None = None
) -> APIRouter:
    """A router wrapping `router`, with the deprecation headers on every response."""
    if sunset <= since:
        raise ValueError("sunset must come after the deprecation date")
    values = headers(since, sunset, successor)

    async def mark(response: Response) -> None:
        response.headers.update(values)

    wrapper = APIRouter(dependencies=[Depends(mark)], deprecated=True)
    wrapper.include_router(router)
    return wrapper

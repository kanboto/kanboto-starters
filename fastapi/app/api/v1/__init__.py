"""Version 1 of the public API (`/api/v1`). A breaking change opens `/api/v2`; v1 is then deprecated with a
removal date (`Deprecation` and `Sunset` headers, `deprecated` in the spec)."""

from fastapi import APIRouter

from app.api.v1 import items

router = APIRouter(prefix="/api/v1")
router.include_router(items.router)

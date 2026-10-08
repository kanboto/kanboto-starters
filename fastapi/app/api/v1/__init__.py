"""Version 1 de l'API publique (`/api/v1`). Un changement cassant ouvre `/api/v2` ; v1 est alors dépréciée
avec une date de retrait (en-têtes `Deprecation` et `Sunset`, `deprecated` dans la spec)."""

from fastapi import APIRouter

from app.api.v1 import items

router = APIRouter(prefix="/api/v1")
router.include_router(items.router)

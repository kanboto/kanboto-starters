"""Example model: replace it with your domain's, keeping its conventions (UUID key, UTC dates)."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from common.db import Base, UtcDateTime, utcnow


class Item(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, index=True)

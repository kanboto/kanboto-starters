"""Idempotency keys of an API (`Idempotency-Key`), kept in the database: any instance can replay them."""

from datetime import datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.db import Base, UtcDateTime, utcnow


class IdempotencyKey(Base):
    """Response to a creation, stored with the client's key: a retry replays it."""

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, index=True)

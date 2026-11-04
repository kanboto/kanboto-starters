"""Database sessions as FastAPI dependencies, over the pools of `common.db`.

A handler that only reads uses `ReadSession`; a handler that writes uses `WriteSession` for all its work,
including the reads it needs to decide. A write returns the updated resource, so clients need not read it
back from a replica that may lag slightly behind.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common import db

WriteSession = Annotated[AsyncSession, Depends(db.write_session)]
ReadSession = Annotated[AsyncSession, Depends(db.read_session)]

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UmfrageOut(BaseModel):
    id: uuid.UUID
    leistungsschein_id: uuid.UUID
    customer_id: uuid.UUID
    versandzeit: Optional[datetime] = None
    erinnert_am: Optional[datetime] = None
    status: str
    bewertung: Optional[int] = None
    kommentar: Optional[str] = None
    beantwortet_am: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UmfrageAntwort(BaseModel):
    bewertung: int = Field(ge=1, le=5)
    kommentar: Optional[str] = None

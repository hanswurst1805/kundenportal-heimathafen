from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class StatusRegelOut(BaseModel):
    id: uuid.UUID
    ereignis_typ: str
    ziel_status_kunde: str
    benachrichtigung: str
    aktiv: bool
    beschreibung: Optional[str] = None

    model_config = {"from_attributes": True}


class StatusRegelUpdate(BaseModel):
    ziel_status_kunde: Optional[str] = None
    benachrichtigung: Optional[str] = None
    aktiv: Optional[bool] = None
    beschreibung: Optional[str] = None

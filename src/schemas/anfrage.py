from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnfrageCreate(BaseModel):
    thema: str
    beschreibung: Optional[str] = None
    fachbereich: Optional[str] = None
    prioritaet: str = "mittel"


class AnfrageOut(BaseModel):
    id: uuid.UUID
    anfrage_nr: str
    customer_id: uuid.UUID
    thema: str
    beschreibung: Optional[str] = None
    fachbereich: Optional[str] = None
    prioritaet: str
    status_kunde: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnfrageInternOut(AnfrageOut):
    ersteller_id: Optional[uuid.UUID] = None
    status_intern: Optional[str] = None
    angebot_id: Optional[uuid.UUID] = None


class AnfrageInternUpdate(BaseModel):
    fachbereich: Optional[str] = None
    prioritaet: Optional[str] = None
    status_intern: Optional[str] = None
    status_kunde: Optional[str] = None

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class BestellungCreate(BaseModel):
    leistung_id: uuid.UUID


class BestellungOut(BaseModel):
    id: uuid.UUID
    bestell_nr: str
    customer_id: uuid.UUID
    leistung_id: uuid.UUID
    besteller_id: uuid.UUID | None = None
    bestelldatum: datetime
    status: str
    angebot_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}

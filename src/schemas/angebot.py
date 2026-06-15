from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class AngebotPositionIn(BaseModel):
    bezeichnung: str
    menge: Decimal = Decimal("1")
    einzelpreis: Decimal = Decimal("0")
    sort_order: int = 0


class AngebotPositionOut(AngebotPositionIn):
    id: uuid.UUID
    gesamtpreis: Decimal

    model_config = {"from_attributes": True}


class AngebotCreate(BaseModel):
    customer_id: uuid.UUID
    anfrage_id: Optional[uuid.UUID] = None
    leistung_id: Optional[uuid.UUID] = None
    titel: str
    gueltig_bis: Optional[date] = None
    positionen: list[AngebotPositionIn] = []


class AngebotUpdate(BaseModel):
    titel: Optional[str] = None
    gueltig_bis: Optional[date] = None
    positionen: Optional[list[AngebotPositionIn]] = None


class AngebotOut(BaseModel):
    id: uuid.UUID
    angebotsnummer: str
    version: int
    customer_id: uuid.UUID
    anfrage_id: Optional[uuid.UUID] = None
    leistung_id: Optional[uuid.UUID] = None
    titel: str
    gueltig_bis: Optional[date] = None
    gesamtpreis: Decimal
    status: str
    positionen: list[AngebotPositionOut] = []

    model_config = {"from_attributes": True}


class AngebotAblehnenRequest(BaseModel):
    begruendung: Optional[str] = None

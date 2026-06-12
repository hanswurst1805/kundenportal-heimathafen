from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LeistungOut(BaseModel):
    id: uuid.UUID
    leistungs_id: str
    name: str
    beschreibung: Optional[str] = None
    kategorie: Optional[str] = None
    preis: Decimal
    preiseinheit: str
    avv_erforderlich: bool
    ist_bestellbar: bool
    is_active: bool

    model_config = {"from_attributes": True}


class LeistungCreate(BaseModel):
    leistungs_id: str
    name: str
    beschreibung: Optional[str] = None
    kategorie: Optional[str] = None
    preis: Decimal = Decimal("0")
    preiseinheit: str = "einmalig"
    avv_erforderlich: bool = False
    ist_bestellbar: bool = True
    is_active: bool = True


class LeistungUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    kategorie: Optional[str] = None
    preis: Optional[Decimal] = None
    preiseinheit: Optional[str] = None
    avv_erforderlich: Optional[bool] = None
    ist_bestellbar: Optional[bool] = None
    is_active: Optional[bool] = None

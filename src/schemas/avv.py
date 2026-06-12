from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel


class AVVOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    bezugstyp: str
    bezugs_id: uuid.UUID
    pflicht: bool
    vorlage_id: Optional[uuid.UUID] = None
    version: Optional[str] = None
    status: str
    signaturvorgang_id: Optional[uuid.UUID] = None
    abschlussdatum: Optional[date] = None

    model_config = {"from_attributes": True}


class AVVVorlageOut(BaseModel):
    id: uuid.UUID
    name: str
    version: str
    inhalt: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class AVVVorlageCreate(BaseModel):
    name: str
    version: str = "1.0"
    inhalt: Optional[str] = None
    is_active: bool = True


class AVVVorlageUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    inhalt: Optional[str] = None
    is_active: Optional[bool] = None

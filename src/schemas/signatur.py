from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SignaturInput(BaseModel):
    """Optionaler Body beim Signieren – fuer den inhouse-Provider mit
    handschriftlicher Unterschrift (PNG-Data-URL) und Unterzeichnername."""

    signatur_bild: Optional[str] = None
    unterzeichner_name: Optional[str] = None


class SignaturvorgangOut(BaseModel):
    id: uuid.UUID
    bezugstyp: str
    bezugs_id: uuid.UUID
    anbieter: str
    token: Optional[str] = None
    signatur_link: Optional[str] = None
    status: str
    versandzeit: Optional[datetime] = None
    signierzeit: Optional[datetime] = None
    erinnerung_gesendet_am: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OffeneSignaturOut(BaseModel):
    """Verdichtete Sicht fuer die Kunden-Liste 'Zu signieren'."""

    id: uuid.UUID
    bezugstyp: str
    token: Optional[str] = None
    status: str
    titel: str

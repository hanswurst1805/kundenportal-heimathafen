from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

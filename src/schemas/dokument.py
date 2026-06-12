from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DokumentOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    typ: str
    version: int
    sichtbarkeit: str
    dateiname: str
    bezugstyp: Optional[str] = None
    bezugs_id: Optional[uuid.UUID] = None
    leistungsschein_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}

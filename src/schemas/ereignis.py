from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EreignisOut(BaseModel):
    id: uuid.UUID
    zeit: datetime
    customer_id: Optional[uuid.UUID] = None
    akteur_id: Optional[uuid.UUID] = None
    akteur_typ: str
    ereignis_typ: str
    bezugstyp: Optional[str] = None
    bezugs_id: Optional[uuid.UUID] = None
    vorher_status: Optional[str] = None
    nachher_status: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    verarbeitet: bool

    model_config = {"from_attributes": True}

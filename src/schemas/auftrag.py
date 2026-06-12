from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuftragOut(BaseModel):
    id: uuid.UUID
    auftragsnummer: str
    customer_id: uuid.UUID
    ursprung_typ: str
    ursprung_id: uuid.UUID
    status: str
    freigabedatum: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuftragsbestaetigungOut(BaseModel):
    id: uuid.UUID
    auftrag_id: uuid.UUID
    dokument_id: Optional[uuid.UUID] = None
    bereitgestellt_am: Optional[datetime] = None
    kenntnisnahme_am: Optional[datetime] = None

    model_config = {"from_attributes": True}

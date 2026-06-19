from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.schemas.angebot import AngebotOut
from src.schemas.auftrag import AuftragOut, AuftragsbestaetigungOut
from src.schemas.avv import AVVOut
from src.schemas.signatur import OffeneSignaturOut


class VorgangOut(BaseModel):
    """Verdichtete Vorgangssicht (Liste): ein Vorgang = Anfrage- oder Bestellungs-Wurzel."""

    typ: str  # anfrage | bestellung
    root_id: uuid.UUID
    referenz: str
    titel: str
    status_kunde: str  # effektiver Gesamtstatus über die ganze Kette
    created_at: datetime
    angebot_id: Optional[uuid.UUID] = None
    avv_id: Optional[uuid.UUID] = None
    auftrag_id: Optional[uuid.UUID] = None
    leistungsschein_id: Optional[uuid.UUID] = None
    auftragsbestaetigung_vorhanden: bool = False
    offene_signatur_token: Optional[str] = None


class VorgangDetailOut(VorgangOut):
    """Vollständige Vorgangssicht (Detail) mit eingebetteten Artefakten."""

    angebot: Optional[AngebotOut] = None
    avv: Optional[AVVOut] = None
    auftrag: Optional[AuftragOut] = None
    auftragsbestaetigung: Optional[AuftragsbestaetigungOut] = None
    leistungsschein_status: Optional[str] = None
    offene_signaturen: list[OffeneSignaturOut] = []

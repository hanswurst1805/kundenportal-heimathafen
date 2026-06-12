"""Erzeugt aus einem angenommenen Angebot/AVV-Abschluss automatisch Auftrag,
Leistungsschein und Auftragsbestaetigung und stoesst die Zielsystem-Uebertragung an."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_target_system_adapter
from src.models.auftrag import AUFTRAG_WIRKSAM, URSPRUNG_ANGEBOT, URSPRUNG_BESTELLUNG, Auftrag, Auftragsbestaetigung
from src.models.leistungsschein import Leistungsschein
from src.services.origin import Origin
from src.services.numbering import next_number


async def create_auftrag_und_leistungsschein(
    session: AsyncSession,
    *,
    customer_id: uuid.UUID,
    origin: Optional[Origin],
    leistung_id: Optional[uuid.UUID],
    scope_beschreibung: Optional[str] = None,
) -> tuple[Auftrag, Leistungsschein]:
    from src.models.anfrage import Anfrage

    if isinstance(origin, Anfrage):
        ursprung_typ = URSPRUNG_ANGEBOT
        ursprung_id = origin.angebot_id or origin.id
    elif origin is not None:
        ursprung_typ = URSPRUNG_BESTELLUNG
        ursprung_id = origin.id
    else:
        ursprung_typ = URSPRUNG_BESTELLUNG
        ursprung_id = uuid.uuid4()

    auftragsnummer = await next_number(session, Auftrag, "AUF")
    auftrag = Auftrag(
        auftragsnummer=auftragsnummer,
        customer_id=customer_id,
        ursprung_typ=ursprung_typ,
        ursprung_id=ursprung_id,
        status=AUFTRAG_WIRKSAM,
        freigabedatum=datetime.now(timezone.utc),
    )
    session.add(auftrag)
    await session.flush()

    ls_nummer = await next_number(session, Leistungsschein, "LS")
    leistungsschein = Leistungsschein(
        ls_nummer=ls_nummer,
        auftrag_id=auftrag.id,
        customer_id=customer_id,
        leistung_id=leistung_id,
        scope_beschreibung=scope_beschreibung,
        status_kunde="beauftragt",
    )
    session.add(leistungsschein)
    await session.flush()

    bestaetigung = Auftragsbestaetigung(
        auftrag_id=auftrag.id, bereitgestellt_am=datetime.now(timezone.utc)
    )
    session.add(bestaetigung)
    await session.flush()

    await get_target_system_adapter().push_order(session, auftrag)

    return auftrag, leistungsschein

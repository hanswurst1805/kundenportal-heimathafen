"""Ermittelt den Mandanten (Customer) zu einem Signaturvorgang anhand seines
polymorphen bezugstyp/bezugs_id-Paares."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.angebot import Angebot
from src.models.auftrag import Auftrag, Auftragsbestaetigung
from src.models.avv import AVV
from src.models.bestellung import Bestellung
from src.models.signatur import (
    BEZUG_ANGEBOT,
    BEZUG_AUFTRAGSBESTAETIGUNG,
    BEZUG_AVV,
    BEZUG_BESTELLUNG,
    Signaturvorgang,
)


async def resolve_customer_id(session: AsyncSession, vorgang: Signaturvorgang) -> Optional[uuid.UUID]:
    if vorgang.bezugstyp == BEZUG_ANGEBOT:
        angebot = await session.get(Angebot, vorgang.bezugs_id)
        return angebot.customer_id if angebot else None
    if vorgang.bezugstyp == BEZUG_BESTELLUNG:
        bestellung = await session.get(Bestellung, vorgang.bezugs_id)
        return bestellung.customer_id if bestellung else None
    if vorgang.bezugstyp == BEZUG_AVV:
        avv = await session.get(AVV, vorgang.bezugs_id)
        return avv.customer_id if avv else None
    if vorgang.bezugstyp == BEZUG_AUFTRAGSBESTAETIGUNG:
        bestaetigung = await session.get(Auftragsbestaetigung, vorgang.bezugs_id)
        if not bestaetigung:
            return None
        auftrag = await session.get(Auftrag, bestaetigung.auftrag_id)
        return auftrag.customer_id if auftrag else None
    return None

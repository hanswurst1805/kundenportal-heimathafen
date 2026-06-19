"""Aggregiert die lose gekoppelten Fachobjekte (Anfrage/Bestellung → Angebot →
AVV → Auftrag/Auftragsbestaetigung → Leistungsschein) zu einem durchgaengigen
'Vorgang' fuer die Kundensicht, inkl. effektivem Gesamtstatus."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.status_codes import KUNDENSTATUS
from src.models.anfrage import Anfrage
from src.models.angebot import Angebot
from src.models.auftrag import Auftrag, Auftragsbestaetigung
from src.models.avv import AVV
from src.models.bestellung import Bestellung
from src.models.leistung import Leistung
from src.models.leistungsschein import Leistungsschein
from src.models.signatur import SIGNATUR_ERSTELLT, SIGNATUR_VERSENDET, Signaturvorgang

VORGANG_ANFRAGE = "anfrage"
VORGANG_BESTELLUNG = "bestellung"


@dataclass
class VorgangDaten:
    typ: str
    root_id: uuid.UUID
    referenz: str
    titel: str
    status_kunde: str
    created_at: datetime
    angebot: Optional[Angebot] = None
    avv: Optional[AVV] = None
    auftrag: Optional[Auftrag] = None
    auftragsbestaetigung: Optional[Auftragsbestaetigung] = None
    leistungsschein: Optional[Leistungsschein] = None
    offene_signaturen: list[Signaturvorgang] = field(default_factory=list)


def _max_status(*werte: Optional[str]) -> str:
    """Effektiver Status = am weitesten fortgeschrittene Stufe im KUNDENSTATUS-Modell."""
    best_index = -1
    bekannt = list(KUNDENSTATUS)
    for wert in werte:
        if wert in bekannt:
            idx = bekannt.index(wert)
            if idx > best_index:
                best_index = idx
    if best_index >= 0:
        return bekannt[best_index]
    for wert in werte:
        if wert:
            return wert
    return KUNDENSTATUS[0]


async def _angebot_mit_positionen(session: AsyncSession, angebot_id: Optional[uuid.UUID]) -> Optional[Angebot]:
    if not angebot_id:
        return None
    return (
        await session.execute(
            select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
        )
    ).scalar_one_or_none()


async def _auftrag_fuer(
    session: AsyncSession, customer_id: uuid.UUID, kandidaten_ids: list[uuid.UUID]
) -> Optional[Auftrag]:
    kandidaten = [k for k in kandidaten_ids if k]
    if not kandidaten:
        return None
    return (
        await session.execute(
            select(Auftrag)
            .where(Auftrag.customer_id == customer_id, Auftrag.ursprung_id.in_(kandidaten))
            .order_by(Auftrag.created_at.desc())
        )
    ).scalars().first()


async def _baue_vorgang(
    session: AsyncSession,
    *,
    typ: str,
    root_id: uuid.UUID,
    customer_id: uuid.UUID,
    referenz: str,
    titel: str,
    root_status: str,
    created_at: datetime,
    angebot_id: Optional[uuid.UUID],
) -> VorgangDaten:
    angebot = await _angebot_mit_positionen(session, angebot_id)

    auftrag = await _auftrag_fuer(session, customer_id, [angebot_id, root_id])
    auftragsbestaetigung = None
    leistungsschein = None
    if auftrag:
        auftragsbestaetigung = (
            await session.execute(
                select(Auftragsbestaetigung).where(Auftragsbestaetigung.auftrag_id == auftrag.id)
            )
        ).scalar_one_or_none()
        leistungsschein = (
            await session.execute(
                select(Leistungsschein)
                .where(Leistungsschein.auftrag_id == auftrag.id)
                .options(
                    selectinload(Leistungsschein.aufgaben),
                    selectinload(Leistungsschein.workshops),
                )
            )
        ).scalar_one_or_none()

    bezug_ids = [i for i in [root_id, angebot_id, auftrag.id if auftrag else None] if i]
    avv = (
        await session.execute(
            select(AVV).where(AVV.customer_id == customer_id, AVV.bezugs_id.in_(bezug_ids))
            .order_by(AVV.created_at.desc())
        )
    ).scalars().first()

    alle_bezug_ids = bezug_ids + [
        i
        for i in [
            avv.id if avv else None,
            auftragsbestaetigung.id if auftragsbestaetigung else None,
            leistungsschein.id if leistungsschein else None,
        ]
        if i
    ]
    offene_signaturen = (
        await session.execute(
            select(Signaturvorgang)
            .where(
                Signaturvorgang.bezugs_id.in_(alle_bezug_ids),
                Signaturvorgang.status.in_([SIGNATUR_ERSTELLT, SIGNATUR_VERSENDET]),
            )
            .order_by(Signaturvorgang.created_at.desc())
        )
    ).scalars().all()

    status = _max_status(root_status, leistungsschein.status_kunde if leistungsschein else None)

    return VorgangDaten(
        typ=typ,
        root_id=root_id,
        referenz=referenz,
        titel=titel,
        status_kunde=status,
        created_at=created_at,
        angebot=angebot,
        avv=avv,
        auftrag=auftrag,
        auftragsbestaetigung=auftragsbestaetigung,
        leistungsschein=leistungsschein,
        offene_signaturen=list(offene_signaturen),
    )


async def list_vorgaenge(session: AsyncSession, customer_id: uuid.UUID) -> list[VorgangDaten]:
    anfragen = (
        await session.execute(
            select(Anfrage).where(Anfrage.customer_id == customer_id)
        )
    ).scalars().all()
    bestellungen = (
        await session.execute(
            select(Bestellung).where(Bestellung.customer_id == customer_id)
        )
    ).scalars().all()

    vorgaenge: list[VorgangDaten] = []
    for a in anfragen:
        vorgaenge.append(
            await _baue_vorgang(
                session,
                typ=VORGANG_ANFRAGE,
                root_id=a.id,
                customer_id=customer_id,
                referenz=a.anfrage_nr,
                titel=a.thema,
                root_status=a.status_kunde,
                created_at=a.created_at,
                angebot_id=a.angebot_id,
            )
        )
    for b in bestellungen:
        leistung = await session.get(Leistung, b.leistung_id)
        vorgaenge.append(
            await _baue_vorgang(
                session,
                typ=VORGANG_BESTELLUNG,
                root_id=b.id,
                customer_id=customer_id,
                referenz=b.bestell_nr,
                titel=leistung.name if leistung else "Bestellung",
                root_status=b.status,
                created_at=b.created_at,
                angebot_id=b.angebot_id,
            )
        )

    vorgaenge.sort(key=lambda v: v.created_at, reverse=True)
    return vorgaenge


async def get_vorgang(
    session: AsyncSession, customer_id: uuid.UUID, typ: str, root_id: uuid.UUID
) -> Optional[VorgangDaten]:
    if typ == VORGANG_ANFRAGE:
        a = await session.get(Anfrage, root_id)
        if not a or a.customer_id != customer_id:
            return None
        return await _baue_vorgang(
            session,
            typ=VORGANG_ANFRAGE,
            root_id=a.id,
            customer_id=customer_id,
            referenz=a.anfrage_nr,
            titel=a.thema,
            root_status=a.status_kunde,
            created_at=a.created_at,
            angebot_id=a.angebot_id,
        )
    if typ == VORGANG_BESTELLUNG:
        b = await session.get(Bestellung, root_id)
        if not b or b.customer_id != customer_id:
            return None
        leistung = await session.get(Leistung, b.leistung_id)
        return await _baue_vorgang(
            session,
            typ=VORGANG_BESTELLUNG,
            root_id=b.id,
            customer_id=customer_id,
            referenz=b.bestell_nr,
            titel=leistung.name if leistung else "Bestellung",
            root_status=b.status,
            created_at=b.created_at,
            angebot_id=b.angebot_id,
        )
    return None

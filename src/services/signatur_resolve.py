"""Ermittelt den Mandanten (Customer) zu einem Signaturvorgang anhand seines
polymorphen bezugstyp/bezugs_id-Paares."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.angebot import Angebot
from src.models.auftrag import Auftrag, Auftragsbestaetigung
from src.models.avv import AVV
from src.models.bestellung import Bestellung
from src.models.customer import Customer
from src.models.leistung import Leistung
from src.models.signatur import (
    BEZUG_ANGEBOT,
    BEZUG_AUFTRAGSBESTAETIGUNG,
    BEZUG_AVV,
    BEZUG_BESTELLUNG,
    Signaturvorgang,
)
from src.services.pdf_signing import DokumentInhalt


async def resolve_titel(session: AsyncSession, vorgang: Signaturvorgang) -> str:
    """Menschlich lesbares Label fuer einen Signaturvorgang (fuer Listen)."""
    if vorgang.bezugstyp == BEZUG_ANGEBOT:
        angebot = await session.get(Angebot, vorgang.bezugs_id)
        if not angebot:
            return "Angebot"
        return f"Angebot {angebot.angebotsnummer}" + (f" – {angebot.titel}" if angebot.titel else "")
    if vorgang.bezugstyp == BEZUG_BESTELLUNG:
        bestellung = await session.get(Bestellung, vorgang.bezugs_id)
        return f"Bestellung {bestellung.bestell_nr}" if bestellung else "Bestellung"
    if vorgang.bezugstyp == BEZUG_AVV:
        return "Auftragsverarbeitungsvertrag"
    if vorgang.bezugstyp == BEZUG_AUFTRAGSBESTAETIGUNG:
        bestaetigung = await session.get(Auftragsbestaetigung, vorgang.bezugs_id)
        if bestaetigung:
            auftrag = await session.get(Auftrag, bestaetigung.auftrag_id)
            if auftrag:
                return f"Auftragsbestätigung {auftrag.auftragsnummer}"
        return "Auftragsbestätigung"
    return vorgang.bezugstyp


async def build_dokument_inhalt(
    session: AsyncSession, vorgang: Signaturvorgang, customer_id: uuid.UUID
) -> DokumentInhalt:
    """Baut die anzuzeigenden Dokumentdaten zu einem Signaturvorgang – genutzt
    fuer die Vorschau (vor dem Signieren) und das signierte PDF."""
    customer = await session.get(Customer, customer_id)
    kunde = customer.name if customer else str(customer_id)

    titel = vorgang.bezugstyp.capitalize()
    referenz = str(vorgang.bezugs_id)[:8]
    zeilen: list[tuple[str, str]] = []

    if vorgang.bezugstyp == BEZUG_ANGEBOT:
        angebot = (
            await session.execute(
                select(Angebot)
                .where(Angebot.id == vorgang.bezugs_id)
                .options(selectinload(Angebot.positionen))
            )
        ).scalar_one_or_none()
        if angebot:
            titel = f"Angebot {angebot.angebotsnummer}"
            referenz = angebot.angebotsnummer
            zeilen = [("Titel", angebot.titel)]
            for pos in angebot.positionen:
                zeilen.append(
                    (pos.bezeichnung, f"{pos.menge} × {pos.einzelpreis} € = {pos.gesamtpreis} €")
                )
            zeilen.append(("Gesamtpreis", f"{angebot.gesamtpreis} €"))
    elif vorgang.bezugstyp == BEZUG_BESTELLUNG:
        bestellung = await session.get(Bestellung, vorgang.bezugs_id)
        if bestellung:
            titel = f"Bestellung {bestellung.bestell_nr}"
            referenz = bestellung.bestell_nr
            leistung = (
                await session.get(Leistung, bestellung.leistung_id)
                if bestellung.leistung_id
                else None
            )
            zeilen = [("Leistung", leistung.name if leistung else "—")]
    elif vorgang.bezugstyp == BEZUG_AVV:
        avv = await session.get(AVV, vorgang.bezugs_id)
        if avv:
            titel = "Auftragsverarbeitungsvertrag (AVV)"
            referenz = str(avv.id)[:8]
            zeilen = [("Version", avv.version or "—"), ("Status", avv.status)]
    elif vorgang.bezugstyp == BEZUG_AUFTRAGSBESTAETIGUNG:
        bestaetigung = await session.get(Auftragsbestaetigung, vorgang.bezugs_id)
        auftrag = (
            await session.get(Auftrag, bestaetigung.auftrag_id) if bestaetigung else None
        )
        if auftrag:
            titel = f"Auftragsbestätigung {auftrag.auftragsnummer}"
            referenz = auftrag.auftragsnummer

    return DokumentInhalt(titel=titel, referenz=referenz, kunde=kunde, zeilen=zeilen)


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

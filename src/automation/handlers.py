"""Handler fuer die 9 Trigger der Statusautomatisierung aus dem Fachkonzept."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_avv_workflow
from src.core.status_codes import (
    EVENT_AVV_COMPLETED,
    EVENT_AVV_REQUIRED,
    EVENT_CUSTOMER_INPUT_REQUIRED,
    EVENT_DELIVERY_COMPLETED,
    EVENT_KICKOFF_SCHEDULED,
    EVENT_ONBOARDING_WORKSHOP_FINISHED,
    EVENT_ONBOARDING_WORKSHOP_SCHEDULED,
    EVENT_SIGNATURE_COMPLETED,
    EVENT_SURVEY_SENT,
)
from src.models.angebot import ANGEBOT_ANGENOMMEN, Angebot
from src.models.auftrag import Auftragsbestaetigung
from src.models.avv import AVV, AVV_ABGESCHLOSSEN, AVVVorlage
from src.models.ereignis import Ereignisprotokoll
from src.models.leistung import Leistung
from src.models.leistungsschein import Leistungsschein
from src.models.signatur import BEZUG_ANGEBOT, BEZUG_AUFTRAGSBESTAETIGUNG, BEZUG_AVV
from src.models.umfrage import UMFRAGE_GEPLANT, UMFRAGE_VERSENDET, Umfrage
from src.services.auftrag_service import create_auftrag_und_leistungsschein
from src.services.origin import find_origin_for_angebot, set_origin_status


async def _set_ls_status(
    session: AsyncSession, eintrag: Ereignisprotokoll, status_kunde: str
) -> Optional[Leistungsschein]:
    ls = await session.get(Leistungsschein, eintrag.bezugs_id) if eintrag.bezugs_id else None
    if not ls:
        return None
    eintrag.vorher_status = ls.status_kunde
    ls.status_kunde = status_kunde
    eintrag.nachher_status = status_kunde
    if not eintrag.customer_id:
        eintrag.customer_id = ls.customer_id
    return ls


async def _handle_angebot_signiert(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    angebot = await session.get(Angebot, eintrag.bezugs_id)
    if not angebot:
        return
    angebot.status = ANGEBOT_ANGENOMMEN

    origin = await find_origin_for_angebot(session, angebot)
    leistung = await session.get(Leistung, angebot.leistung_id) if angebot.leistung_id else None
    avv_pflicht = await get_avv_workflow().determine_requirement(leistung) if leistung else False

    bestehende_avv = (
        await session.execute(
            select(AVV).where(AVV.bezugstyp == BEZUG_ANGEBOT, AVV.bezugs_id == angebot.id)
        )
    ).scalar_one_or_none()

    if avv_pflicht and (not bestehende_avv or bestehende_avv.status != AVV_ABGESCHLOSSEN):
        from src.automation.events import publish

        await publish(
            session,
            EVENT_AVV_REQUIRED,
            customer_id=angebot.customer_id,
            bezugstyp=BEZUG_ANGEBOT,
            bezugs_id=angebot.id,
            payload={"angebot_id": str(angebot.id)},
        )
        eintrag.nachher_status = "avv_ausstehend"
        eintrag.customer_id = angebot.customer_id
        if origin:
            set_origin_status(origin, "avv_ausstehend")
    else:
        await create_auftrag_und_leistungsschein(
            session,
            customer_id=angebot.customer_id,
            origin=origin,
            leistung_id=angebot.leistung_id,
            scope_beschreibung=angebot.titel,
        )
        eintrag.nachher_status = "beauftragt"
        eintrag.customer_id = angebot.customer_id
        if origin:
            set_origin_status(origin, "beauftragt")


async def _handle_avv_signiert(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    """Wird sowohl als 'signature_completed' (bezugstyp=avv) als auch direkt
    als 'avv_completed' aufgerufen; bezugs_id ist in beiden Faellen die AVV-ID."""
    avv = await session.get(AVV, eintrag.bezugs_id)
    if not avv:
        return
    avv.status = AVV_ABGESCHLOSSEN
    avv.abschlussdatum = date.today()

    angebot = (
        await session.get(Angebot, avv.bezugs_id) if avv.bezugstyp == BEZUG_ANGEBOT else None
    )
    origin = await find_origin_for_angebot(session, angebot) if angebot else None
    leistung_id = angebot.leistung_id if angebot else None

    await create_auftrag_und_leistungsschein(
        session,
        customer_id=avv.customer_id,
        origin=origin,
        leistung_id=leistung_id,
        scope_beschreibung=angebot.titel if angebot else None,
    )
    eintrag.nachher_status = "beauftragt"
    eintrag.customer_id = avv.customer_id
    if origin:
        set_origin_status(origin, "beauftragt")


async def _handle_signature_completed(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    if eintrag.bezugstyp == BEZUG_ANGEBOT:
        await _handle_angebot_signiert(session, eintrag)
    elif eintrag.bezugstyp == BEZUG_AVV:
        await _handle_avv_signiert(session, eintrag)
    elif eintrag.bezugstyp == BEZUG_AUFTRAGSBESTAETIGUNG:
        bestaetigung = (
            await session.execute(
                select(Auftragsbestaetigung).where(Auftragsbestaetigung.auftrag_id == eintrag.bezugs_id)
            )
        ).scalar_one_or_none()
        if bestaetigung:
            bestaetigung.kenntnisnahme_am = datetime.now(timezone.utc)


async def _handle_avv_required(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    angebot = await session.get(Angebot, eintrag.bezugs_id)
    if not angebot:
        return
    vorlage = (
        (await session.execute(select(AVVVorlage).where(AVVVorlage.is_active.is_(True))))
        .scalars()
        .first()
    )
    await get_avv_workflow().create_avv(
        session,
        customer_id=angebot.customer_id,
        bezugstyp=BEZUG_ANGEBOT,
        bezugs_id=angebot.id,
        vorlage=vorlage,
    )
    eintrag.nachher_status = "avv_ausstehend"
    eintrag.customer_id = angebot.customer_id


async def _handle_kickoff_scheduled(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    await _set_ls_status(session, eintrag, "kickoff_gestartet")


async def _handle_onboarding_workshop_scheduled(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    await _set_ls_status(session, eintrag, "onboarding_workshop")


async def _handle_onboarding_workshop_finished(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    await _set_ls_status(session, eintrag, "in_bearbeitung")


async def _handle_customer_input_required(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    await _set_ls_status(session, eintrag, "warten_auf_kunde")


async def _handle_delivery_completed(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    ls = await _set_ls_status(session, eintrag, "fertiggestellt")
    if not ls:
        return

    umfrage = Umfrage(leistungsschein_id=ls.id, customer_id=ls.customer_id, status=UMFRAGE_GEPLANT)
    session.add(umfrage)
    await session.flush()

    from src.automation.events import publish

    await publish(
        session,
        EVENT_SURVEY_SENT,
        customer_id=ls.customer_id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        payload={"umfrage_id": str(umfrage.id)},
    )


async def _handle_survey_sent(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    ls = await _set_ls_status(session, eintrag, "kundenzufriedenheitsabfrage")
    if not ls:
        return
    umfrage = (
        (
            await session.execute(
                select(Umfrage)
                .where(Umfrage.leistungsschein_id == ls.id)
                .order_by(Umfrage.created_at.desc())
            )
        )
        .scalars()
        .first()
    )
    if umfrage:
        umfrage.status = UMFRAGE_VERSENDET
        umfrage.versandzeit = datetime.now(timezone.utc)


HANDLERS = {
    EVENT_SIGNATURE_COMPLETED: _handle_signature_completed,
    EVENT_AVV_REQUIRED: _handle_avv_required,
    EVENT_AVV_COMPLETED: _handle_avv_signiert,
    EVENT_KICKOFF_SCHEDULED: _handle_kickoff_scheduled,
    EVENT_ONBOARDING_WORKSHOP_SCHEDULED: _handle_onboarding_workshop_scheduled,
    EVENT_ONBOARDING_WORKSHOP_FINISHED: _handle_onboarding_workshop_finished,
    EVENT_CUSTOMER_INPUT_REQUIRED: _handle_customer_input_required,
    EVENT_DELIVERY_COMPLETED: _handle_delivery_completed,
    EVENT_SURVEY_SENT: _handle_survey_sent,
}

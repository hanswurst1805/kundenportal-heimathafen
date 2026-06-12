"""Unterdrueckt wiederholte, nichtssagende Statusmeldungen an den Kunden."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.status_codes import NOTIFY_JA, NOTIFY_NEIN
from src.models.ereignis import Ereignisprotokoll
from src.models.status import StatusRegel


async def should_notify(session: AsyncSession, eintrag: Ereignisprotokoll, regel: StatusRegel) -> bool:
    if not eintrag.nachher_status:
        return False
    if regel.benachrichtigung == NOTIFY_NEIN:
        return False
    if regel.benachrichtigung == NOTIFY_JA:
        return True

    # "optional": unterdruecken, wenn der letzte Statuswechsel fuer dasselbe
    # Bezugsobjekt bereits denselben Zielstatus gemeldet hat.
    if eintrag.bezugs_id is None:
        return True

    stmt = (
        select(Ereignisprotokoll)
        .where(
            Ereignisprotokoll.bezugs_id == eintrag.bezugs_id,
            Ereignisprotokoll.id != eintrag.id,
            Ereignisprotokoll.nachher_status.isnot(None),
        )
        .order_by(Ereignisprotokoll.zeit.desc())
        .limit(1)
    )
    last = (await session.execute(stmt)).scalar_one_or_none()
    if last and last.nachher_status == eintrag.nachher_status:
        return False
    return True

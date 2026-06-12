"""In-Process Event-Bus: schreibt Ereignisprotokoll-Eintraege, ruft Handler auf
und stoesst (deduplizierte) Kundenbenachrichtigungen an."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_notification_provider
from src.automation.dedup import should_notify
from src.automation.handlers import HANDLERS
from src.automation.rules import get_status_regel
from src.core.status_codes import KUNDENSTATUS_LABELS
from src.models.customer import Customer
from src.models.ereignis import AKTEUR_SYSTEM, Ereignisprotokoll


async def _notify_customer(session: AsyncSession, eintrag: Ereignisprotokoll) -> None:
    if not eintrag.customer_id:
        return
    customer = await session.get(Customer, eintrag.customer_id)
    if not customer or not customer.contact_email:
        return

    status_label = KUNDENSTATUS_LABELS.get(eintrag.nachher_status, eintrag.nachher_status)
    subject = f"Statusupdate: {status_label}"
    body = (
        f"Sehr geehrte/r {customer.contact_name or customer.name},\n\n"
        f"der Status Ihres Vorgangs hat sich geaendert auf: {status_label}.\n\n"
        f"Mit freundlichen Gruessen\nIhr Kundenportal-Team"
    )
    await get_notification_provider().send_email(customer.contact_email, subject, body)

    session.add(
        Ereignisprotokoll(
            customer_id=eintrag.customer_id,
            akteur_typ=AKTEUR_SYSTEM,
            ereignis_typ="notification_sent",
            bezugstyp=eintrag.bezugstyp,
            bezugs_id=eintrag.bezugs_id,
            nachher_status=eintrag.nachher_status,
            payload={"kanal": "email", "ausgeloest_durch": eintrag.ereignis_typ},
            verarbeitet=True,
        )
    )


async def publish(
    session: AsyncSession,
    ereignis_typ: str,
    *,
    customer_id: Optional[uuid.UUID] = None,
    bezugstyp: Optional[str] = None,
    bezugs_id: Optional[uuid.UUID] = None,
    akteur_id: Optional[uuid.UUID] = None,
    akteur_typ: str = AKTEUR_SYSTEM,
    vorher_status: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> Ereignisprotokoll:
    eintrag = Ereignisprotokoll(
        customer_id=customer_id,
        akteur_id=akteur_id,
        akteur_typ=akteur_typ,
        ereignis_typ=ereignis_typ,
        bezugstyp=bezugstyp,
        bezugs_id=bezugs_id,
        vorher_status=vorher_status,
        payload=payload,
        verarbeitet=False,
    )
    session.add(eintrag)
    await session.flush()

    handler = HANDLERS.get(ereignis_typ)
    if handler:
        await handler(session, eintrag)

    regel = await get_status_regel(session, ereignis_typ)
    if regel and regel.aktiv and await should_notify(session, eintrag, regel):
        await _notify_customer(session, eintrag)

    eintrag.verarbeitet = True
    await session.flush()
    return eintrag

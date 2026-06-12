"""Stub-Implementierung: schreibt Integrations-Ereignisse ins Ereignisprotokoll,
ohne ein echtes Zielsystem anzusprechen."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.auftrag import Auftrag
from src.models.ereignis import AKTEUR_ADAPTER, Ereignisprotokoll


class StubTargetSystemAdapter:
    async def push_order(self, session: AsyncSession, auftrag: Auftrag) -> bool:
        session.add(
            Ereignisprotokoll(
                customer_id=auftrag.customer_id,
                akteur_typ=AKTEUR_ADAPTER,
                ereignis_typ="integration_pushed",
                bezugstyp="auftrag",
                bezugs_id=auftrag.id,
                payload={"auftragsnummer": auftrag.auftragsnummer},
                verarbeitet=True,
            )
        )
        await session.flush()
        return True

    async def update_status(self, session: AsyncSession, auftrag: Auftrag, status: str) -> bool:
        session.add(
            Ereignisprotokoll(
                customer_id=auftrag.customer_id,
                akteur_typ=AKTEUR_ADAPTER,
                ereignis_typ="integration_status_update",
                bezugstyp="auftrag",
                bezugs_id=auftrag.id,
                payload={"status": status},
                verarbeitet=True,
            )
        )
        await session.flush()
        return True

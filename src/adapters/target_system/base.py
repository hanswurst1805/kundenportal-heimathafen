"""Schnittstelle fuer das Zielsystem (z.B. PSA/Ticketsystem), in das
beauftragte Auftraege uebertragen werden."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.auftrag import Auftrag


class TargetSystemAdapter(Protocol):
    async def push_order(self, session: AsyncSession, auftrag: Auftrag) -> bool:
        """Uebertraegt einen Auftrag ins Zielsystem. Gibt True bei Erfolg zurueck."""
        ...

    async def update_status(self, session: AsyncSession, auftrag: Auftrag, status: str) -> bool:
        """Aktualisiert den Status im Zielsystem. Gibt True bei Erfolg zurueck."""
        ...

"""Schnittstelle fuer die AVV-Workflow-Pruefung (Art. 28 DSGVO)."""

from __future__ import annotations

import uuid
from typing import Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.avv import AVV, AVVVorlage
from src.models.leistung import Leistung


class AVVWorkflow(Protocol):
    async def determine_requirement(self, leistung: Leistung) -> bool:
        """Prueft, ob fuer eine Leistung ein AVV erforderlich ist."""
        ...

    async def create_avv(
        self,
        session: AsyncSession,
        customer_id: uuid.UUID,
        bezugstyp: str,
        bezugs_id: uuid.UUID,
        vorlage: Optional[AVVVorlage],
    ) -> AVV:
        """Legt einen AVV-Vorgang an und stoesst die Signatur an."""
        ...

    async def get_status(self, avv: AVV) -> str:
        ...

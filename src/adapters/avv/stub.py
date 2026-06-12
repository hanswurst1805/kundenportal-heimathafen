from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.signature.base import SignatureProvider
from src.models.avv import AVV, AVV_AUSSTEHEND, AVVVorlage
from src.models.leistung import Leistung
from src.models.signatur import BEZUG_AVV


class StubAVVWorkflow:
    def __init__(self, signature_provider: SignatureProvider) -> None:
        self._signature_provider = signature_provider

    async def determine_requirement(self, leistung: Leistung) -> bool:
        return bool(leistung.avv_erforderlich)

    async def create_avv(
        self,
        session: AsyncSession,
        customer_id: uuid.UUID,
        bezugstyp: str,
        bezugs_id: uuid.UUID,
        vorlage: Optional[AVVVorlage],
    ) -> AVV:
        avv = AVV(
            customer_id=customer_id,
            bezugstyp=bezugstyp,
            bezugs_id=bezugs_id,
            pflicht=True,
            vorlage_id=vorlage.id if vorlage else None,
            version=vorlage.version if vorlage else None,
            status=AVV_AUSSTEHEND,
        )
        session.add(avv)
        await session.flush()

        vorgang = await self._signature_provider.create_envelope(
            session, BEZUG_AVV, avv.id, "AVV - Vereinbarung zur Auftragsverarbeitung"
        )
        avv.signaturvorgang_id = vorgang.id
        await session.flush()
        return avv

    async def get_status(self, avv: AVV) -> str:
        return avv.status

"""Stub-Implementierung des SignatureProvider: erzeugt einen internen Link
'/sign/{token}', den der Kunde im Portal "unterschreibt" (manuelle Simulation
eines Signatur-Webhooks)."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.signatur import SIGNATUR_ERSTELLT, SIGNATUR_VERSENDET, Signaturvorgang


class StubSignatureProvider:
    async def create_envelope(
        self,
        session: AsyncSession,
        bezugstyp: str,
        bezugs_id: uuid.UUID,
        dokument_name: str,
    ) -> Signaturvorgang:
        vorgang = Signaturvorgang(
            bezugstyp=bezugstyp,
            bezugs_id=bezugs_id,
            anbieter="stub",
            token=secrets.token_urlsafe(16),
            status=SIGNATUR_VERSENDET,
            versandzeit=datetime.now(timezone.utc),
        )
        vorgang.signatur_link = f"/sign/{vorgang.token}"
        session.add(vorgang)
        await session.flush()
        return vorgang

    async def get_status(self, session: AsyncSession, vorgang: Signaturvorgang) -> str:
        return vorgang.status

    async def cancel(self, session: AsyncSession, vorgang: Signaturvorgang) -> None:
        vorgang.status = "abgelehnt"
        await session.flush()

    async def apply_signature(self, session, vorgang, *, unterzeichner_name, signatur_bild, ip_adresse):
        """Stub erzeugt kein Dokument – das Klick-Signieren genuegt."""
        return None

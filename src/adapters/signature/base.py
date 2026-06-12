"""Schnittstelle fuer Signatur-Provider (z.B. DocuSign, Skribble, ...)."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.signatur import Signaturvorgang


class SignatureProvider(Protocol):
    """Erstellt und verwaltet Signaturvorgaenge fuer ein fachliches Objekt
    (Angebot, AVV, Auftragsbestaetigung), referenziert via bezugstyp/bezugs_id."""

    async def create_envelope(
        self,
        session: AsyncSession,
        bezugstyp: str,
        bezugs_id: uuid.UUID,
        dokument_name: str,
    ) -> Signaturvorgang:
        """Legt einen neuen Signaturvorgang an und versendet ihn (Status 'versendet')."""
        ...

    async def get_status(self, session: AsyncSession, vorgang: Signaturvorgang) -> str:
        """Liefert den aktuellen Status des Vorgangs (ggf. Provider-Abfrage)."""
        ...

    async def cancel(self, session: AsyncSession, vorgang: Signaturvorgang) -> None:
        """Bricht einen laufenden Signaturvorgang ab."""
        ...

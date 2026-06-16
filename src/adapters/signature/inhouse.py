"""In-Portal-Signatur-Provider (signature_provider=inhouse).

Erzeugt den Signaturvorgang wie der Stub (interner Link /sign/{token}), erstellt
beim Signieren aber ein echtes, kryptografisch versiegeltes PDF mit der
handschriftlichen Unterschrift des Kunden + Audit-Trail und legt es als Dokument
(kundensichtbar) ab.
"""

from __future__ import annotations

import asyncio
import base64
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dokument import DOK_SIGNATUR_DOKUMENT, SICHTBAR_KUNDE, Dokument
from src.models.signatur import (
    SIGNATUR_ABGELEHNT,
    SIGNATUR_VERSENDET,
    Signaturvorgang,
)
from src.services.pdf_signing import SignaturAudit, erzeuge_signiertes_pdf
from src.services.signatur_resolve import build_dokument_inhalt, resolve_customer_id


def _decode_image(data_url: Optional[str]) -> Optional[bytes]:
    if not data_url:
        return None
    payload = data_url.split(",", 1)[1] if "," in data_url else data_url
    try:
        return base64.b64decode(payload)
    except (ValueError, TypeError):
        return None


class InhouseSignatureProvider:
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
            anbieter="inhouse",
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
        vorgang.status = SIGNATUR_ABGELEHNT
        await session.flush()

    async def apply_signature(
        self,
        session: AsyncSession,
        vorgang: Signaturvorgang,
        *,
        unterzeichner_name: str,
        signatur_bild: Optional[str],
        ip_adresse: Optional[str],
    ) -> Optional[Dokument]:
        """Erzeugt das versiegelte Signatur-PDF und legt es als Dokument ab."""
        customer_id = await resolve_customer_id(session, vorgang)
        if customer_id is None:
            return None

        inhalt = await build_dokument_inhalt(session, vorgang, customer_id)
        audit = SignaturAudit(
            unterzeichner_name=unterzeichner_name,
            signiert_am=datetime.now(timezone.utc),
            ip_adresse=ip_adresse,
            vorgang_id=str(vorgang.id),
        )
        dateiname = f"{inhalt.titel.replace('/', '-')}.pdf"
        # PDF-Erzeugung + kryptografische Versiegelung sind synchron/CPU-lastig
        # (pyhanko nutzt intern asyncio.run) -> in eigenem Thread ausfuehren.
        ablageort = await asyncio.to_thread(
            erzeuge_signiertes_pdf,
            inhalt,
            audit,
            _decode_image(signatur_bild),
            f"signatur-{vorgang.id}.pdf",
        )

        dokument = Dokument(
            customer_id=customer_id,
            typ=DOK_SIGNATUR_DOKUMENT,
            version=1,
            sichtbarkeit=SICHTBAR_KUNDE,
            dateiname=dateiname,
            ablageort=ablageort,
            bezugstyp=vorgang.bezugstyp,
            bezugs_id=vorgang.bezugs_id,
        )
        session.add(dokument)
        await session.flush()
        return dokument

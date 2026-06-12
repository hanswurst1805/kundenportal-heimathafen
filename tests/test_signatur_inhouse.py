"""Test der In-Portal-Signatur (signature_provider=inhouse).

Prueft den InhouseSignatureProvider direkt gegen die Datenbank (unabhaengig vom
am API konfigurierten Provider): create_envelope + apply_signature erzeugen ein
kundensichtbares Dokument mit einem kryptografisch versiegelten PDF (PAdES).

Voraussetzung: erreichbare DB (wie bei den uebrigen Integrationstests).
"""

from __future__ import annotations

import base64
import io
import os
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.asyncio


def _signatur_png_data_url() -> str:
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (300, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(10, 80), (150, 20), (290, 70)], fill=(0, 0, 0, 255), width=4)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


async def test_inhouse_signatur_erzeugt_versiegeltes_pdf():
    from decimal import Decimal

    from pyhanko.pdf_utils.reader import PdfFileReader

    from src.adapters.signature.inhouse import InhouseSignatureProvider
    from src.core.database import get_async_session_factory
    from src.models.bestellung import Bestellung
    from src.models.customer import Customer
    from src.models.dokument import DOK_SIGNATUR_DOKUMENT, SICHTBAR_KUNDE
    from src.models.leistung import Leistung
    from src.models.signatur import BEZUG_BESTELLUNG, SIGNATUR_VERSENDET

    suffix = uuid.uuid4().hex[:8]
    provider = InhouseSignatureProvider()
    ablageort = None

    factory = get_async_session_factory()
    async with factory() as session:
        customer = Customer(
            kundennummer=f"K-{suffix}",
            name="Signatur Testkunde GmbH",
            contact_name="Max Muster",
            contact_email="demo@example.org",
        )
        session.add(customer)
        await session.flush()

        leistung = Leistung(leistungs_id=f"L-{suffix}", name="Managed Workplace", preis=Decimal("49.90"))
        session.add(leistung)
        await session.flush()

        bestellung = Bestellung(
            bestell_nr=f"BES-{suffix}", customer_id=customer.id, leistung_id=leistung.id
        )
        session.add(bestellung)
        await session.flush()

        vorgang = await provider.create_envelope(
            session, BEZUG_BESTELLUNG, bestellung.id, "Beauftragung"
        )
        assert vorgang.anbieter == "inhouse"
        assert vorgang.status == SIGNATUR_VERSENDET
        assert vorgang.token

        dokument = await provider.apply_signature(
            session,
            vorgang,
            unterzeichner_name="Max Muster",
            signatur_bild=_signatur_png_data_url(),
            ip_adresse="198.51.100.9",
        )
        await session.commit()

        assert dokument is not None
        assert dokument.typ == DOK_SIGNATUR_DOKUMENT
        assert dokument.sichtbarkeit == SICHTBAR_KUNDE
        assert dokument.customer_id == customer.id
        ablageort = dokument.ablageort

    try:
        pfad = Path(ablageort)
        assert pfad.is_file()
        data = pfad.read_bytes()
        assert data[:4] == b"%PDF"
        with open(pfad, "rb") as fh:
            sigs = PdfFileReader(fh).embedded_signatures
        assert len(sigs) == 1
        assert sigs[0].field_name == "KundenportalSignatur"
    finally:
        if ablageort and os.path.exists(ablageort):
            os.remove(ablageort)

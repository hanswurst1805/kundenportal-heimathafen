"""In-Portal-Signatur: erzeugt aus einem fachlichen Vorgang ein PDF mit
eingebetteter handschriftlicher Unterschrift + Audit-Trail und versiegelt es
kryptografisch (PAdES) mit pyHanko.

Bewusst ohne externen Dienst – nur Open-Source-Bibliotheken:
- reportlab  -> PDF-Erzeugung (Layout, Unterschrift-Bild, Audit-Trail)
- pyhanko    -> kryptografische PDF-Signatur (Integritaet/Manipulationsschutz = FES)
- cryptography -> selbstsigniertes Siegel-Zertifikat (falls keines konfiguriert)

Das Siegel-Zertifikat repraesentiert den Dienst ("Kundenportal Heimathafen") und
belegt, dass das Dokument nach dem Signieren nicht veraendert wurde. Die Identitaet
des Unterzeichners ergibt sich aus Login + Audit-Trail (Name, Zeit, IP).
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.config import settings


# ---------------------------------------------------------------------------
# Ablage-Verzeichnisse
# ---------------------------------------------------------------------------
def documents_dir() -> Path:
    path = Path(settings.documents_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _signing_dir() -> Path:
    path = documents_dir().parent / "signing"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Siegel-Zertifikat (PKCS#12) – konfiguriert oder selbstsigniert erzeugt
# ---------------------------------------------------------------------------
def _passphrase() -> bytes | None:
    return settings.signing_cert_password.encode() if settings.signing_cert_password else None


def ensure_signing_pkcs12() -> Path:
    """Liefert den Pfad zu einer PKCS#12-Datei mit Siegel-Schluessel/Zertifikat.

    Ist `signing_cert_path` gesetzt, wird diese Datei verwendet. Andernfalls wird
    einmalig ein selbstsigniertes Zertifikat erzeugt und wiederverwendet."""
    if settings.signing_cert_path:
        return Path(settings.signing_cert_path)

    p12_path = _signing_dir() / "kundenportal-signing.p12"
    if p12_path.exists():
        return p12_path

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Kundenportal Heimathafen Signatur"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Heimathafen"),
        ]
    )
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,  # non-repudiation
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    passphrase = _passphrase()
    encryption = (
        serialization.BestAvailableEncryption(passphrase)
        if passphrase
        else serialization.NoEncryption()
    )
    p12_bytes = pkcs12.serialize_key_and_certificates(
        name=b"kundenportal", key=key, cert=cert, cas=None, encryption_algorithm=encryption
    )
    # Restriktive Rechte – enthaelt den privaten Schluessel.
    with open(p12_path, "wb") as fh:
        fh.write(p12_bytes)
    os.chmod(p12_path, 0o600)
    return p12_path


# ---------------------------------------------------------------------------
# PDF-Erzeugung (reportlab)
# ---------------------------------------------------------------------------
@dataclass
class SignaturAudit:
    unterzeichner_name: str
    signiert_am: datetime
    ip_adresse: str | None
    vorgang_id: str


@dataclass
class DokumentInhalt:
    titel: str
    referenz: str
    kunde: str
    zeilen: list[tuple[str, str]] = field(default_factory=list)  # (Label, Wert)


def build_signature_pdf(
    inhalt: DokumentInhalt, audit: SignaturAudit, signatur_png: bytes | None
) -> bytes:
    """Baut ein einseitiges PDF: Kopf, Dokumentdaten, Unterschriftblock."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 25 * mm
    y = height - 30 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left, y, inhalt.titel)
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.setFillGray(0.4)
    c.drawString(left, y, f"Referenz: {inhalt.referenz}    Kunde: {inhalt.kunde}")
    c.setFillGray(0)
    y -= 6 * mm
    c.line(left, y, width - left, y)
    y -= 12 * mm

    c.setFont("Helvetica", 11)
    for label, wert in inhalt.zeilen:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(left + 55 * mm, y, str(wert))
        y -= 7 * mm

    # Unterschriftblock unten
    block_y = 70 * mm
    c.line(left, block_y + 35 * mm, width - left, block_y + 35 * mm)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left, block_y + 28 * mm, "Elektronische Signatur")

    if signatur_png:
        try:
            img = ImageReader(io.BytesIO(signatur_png))
            c.drawImage(
                img, left, block_y, width=70 * mm, height=22 * mm,
                preserveAspectRatio=True, anchor="sw", mask="auto",
            )
        except Exception:  # pragma: no cover - defensiv, falls Bild unlesbar
            pass
    c.line(left, block_y - 2 * mm, left + 70 * mm, block_y - 2 * mm)

    c.setFont("Helvetica", 9)
    c.setFillGray(0.3)
    audit_y = block_y - 8 * mm
    for line in (
        f"Unterzeichner: {audit.unterzeichner_name}",
        f"Zeitpunkt: {audit.signiert_am.strftime('%d.%m.%Y %H:%M:%S %Z')}",
        f"IP-Adresse: {audit.ip_adresse or 'unbekannt'}",
        f"Vorgangs-ID: {audit.vorgang_id}",
        "Das Dokument ist nach dem Signieren kryptografisch versiegelt (PAdES).",
    ):
        c.drawString(left, audit_y, line)
        audit_y -= 5 * mm
    c.setFillGray(0)

    c.showPage()
    c.save()
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Kryptografische Versiegelung (pyhanko / PAdES)
# ---------------------------------------------------------------------------
def seal_pdf(pdf_bytes: bytes, *, reason: str, location: str = "Kundenportal Heimathafen") -> bytes:
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign import signers

    p12_path = ensure_signing_pkcs12()
    signer = signers.SimpleSigner.load_pkcs12(pfx_file=str(p12_path), passphrase=_passphrase())
    if signer is None:  # pragma: no cover - nur bei kaputtem Zertifikat
        raise RuntimeError("Siegel-Zertifikat konnte nicht geladen werden.")

    writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))
    meta = signers.PdfSignatureMetadata(
        field_name="KundenportalSignatur", reason=reason, location=location
    )
    out = signers.sign_pdf(writer, meta, signer=signer)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Orchestrierung: signiertes PDF erzeugen und ablegen
# ---------------------------------------------------------------------------
def erzeuge_signiertes_pdf(
    inhalt: DokumentInhalt, audit: SignaturAudit, signatur_png: bytes | None, dateiname: str
) -> str:
    """Baut + versiegelt das PDF, legt es unter documents_dir ab und gibt den
    absoluten Ablagepfad zurueck."""
    raw = build_signature_pdf(inhalt, audit, signatur_png)
    sealed = seal_pdf(raw, reason=f"Signatur {inhalt.titel}")
    ziel = documents_dir() / dateiname
    with open(ziel, "wb") as fh:
        fh.write(sealed)
    return str(ziel.resolve())

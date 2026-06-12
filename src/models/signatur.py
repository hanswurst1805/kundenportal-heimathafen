from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPKMixin

# Bezugstypen
BEZUG_ANGEBOT = "angebot"
BEZUG_AVV = "avv"
BEZUG_AUFTRAGSBESTAETIGUNG = "auftragsbestaetigung"

# Signaturstatus
SIGNATUR_ERSTELLT = "erstellt"
SIGNATUR_VERSENDET = "versendet"
SIGNATUR_SIGNIERT = "signiert"
SIGNATUR_ABGELEHNT = "abgelehnt"
SIGNATUR_FEHLER = "fehler"
SIGNATUR_ABGELAUFEN = "abgelaufen"


class Signaturvorgang(Base, UUIDPKMixin):
    """Generischer Signaturvorgang fuer Angebote, AVV und Auftragsbestaetigungen.

    bezugstyp/bezugs_id referenzieren das fachliche Objekt polymorph (kein DB-FK,
    da der SignatureProvider-Adapter typneutral arbeitet)."""

    __tablename__ = "signaturvorgaenge"

    bezugstyp: Mapped[str] = mapped_column(String(32), index=True)
    bezugs_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    anbieter: Mapped[str] = mapped_column(String(32), default="stub")
    anbieter_referenz: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    signatur_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=SIGNATUR_ERSTELLT)
    versandzeit: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signierzeit: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    erinnerung_gesendet_am: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

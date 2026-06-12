from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPKMixin

# Auftragsstatus
AUFTRAG_ENTWURF = "entwurf"
AUFTRAG_WIRKSAM = "wirksam"
AUFTRAG_STORNIERT = "storniert"

# Ursprungstypen
URSPRUNG_BESTELLUNG = "bestellung"
URSPRUNG_ANGEBOT = "angebot"


class Auftrag(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "auftraege"

    auftragsnummer: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    ursprung_typ: Mapped[str] = mapped_column(String(32))
    ursprung_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(32), default=AUFTRAG_ENTWURF)
    freigabedatum: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Auftragsbestaetigung(Base, UUIDPKMixin):
    __tablename__ = "auftragsbestaetigungen"

    auftrag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auftraege.id"), unique=True
    )
    dokument_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dokumente.id"), nullable=True
    )
    bereitgestellt_am: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    kenntnisnahme_am: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

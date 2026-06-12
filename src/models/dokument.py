from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPKMixin

# Dokumenttypen
DOK_ANGEBOT = "angebot"
DOK_SIGNATUR_DOKUMENT = "signatur_dokument"
DOK_AVV = "avv"
DOK_AUFTRAGSBESTAETIGUNG = "auftragsbestaetigung"
DOK_SONSTIGES = "sonstiges"

# Sichtbarkeit
SICHTBAR_KUNDE = "kunde"
SICHTBAR_INTERN = "intern"


class Dokument(Base, UUIDPKMixin):
    __tablename__ = "dokumente"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    typ: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    sichtbarkeit: Mapped[str] = mapped_column(String(16), default=SICHTBAR_INTERN)
    dateiname: Mapped[str] = mapped_column(String(255))
    ablageort: Mapped[str] = mapped_column(String(512))
    bezugstyp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bezugs_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    leistungsschein_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungsscheine.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

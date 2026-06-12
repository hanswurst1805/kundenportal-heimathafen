from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPKMixin

# AVV-Status
AVV_NICHT_ERFORDERLICH = "nicht_erforderlich"
AVV_AUSSTEHEND = "ausstehend"
AVV_VERSENDET = "versendet"
AVV_SIGNIERT = "signiert"
AVV_ABGESCHLOSSEN = "abgeschlossen"


class AVVVorlage(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "avv_vorlagen"

    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    inhalt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AVV(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "avv"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    bezugstyp: Mapped[str] = mapped_column(String(32))  # bestellung|anfrage|auftrag
    bezugs_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    pflicht: Mapped[bool] = mapped_column(Boolean, default=False)
    vorlage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("avv_vorlagen.id"), nullable=True
    )
    version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=AVV_NICHT_ERFORDERLICH)
    signaturvorgang_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signaturvorgaenge.id"), nullable=True
    )
    abschlussdatum: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

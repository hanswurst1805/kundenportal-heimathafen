from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPKMixin

# Umfragestatus
UMFRAGE_GEPLANT = "geplant"
UMFRAGE_VERSENDET = "versendet"
UMFRAGE_ERINNERT = "erinnert"
UMFRAGE_BEANTWORTET = "beantwortet"
UMFRAGE_ABGESCHLOSSEN_OHNE_FEEDBACK = "abgeschlossen_ohne_feedback"


class Umfrage(Base, UUIDPKMixin):
    __tablename__ = "umfragen"

    leistungsschein_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungsscheine.id")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    versandzeit: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    erinnert_am: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=UMFRAGE_GEPLANT)
    bewertung: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kommentar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    beantwortet_am: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

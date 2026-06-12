from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPKMixin
from src.core.status_codes import KUNDENSTATUS


class Anfrage(Base, UUIDPKMixin, TimestampMixin):
    """Individuelle Leistungsanfrage eines Kunden."""

    __tablename__ = "anfragen"

    anfrage_nr: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    ersteller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    thema: Mapped[str] = mapped_column(String(255))
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fachbereich: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    prioritaet: Mapped[str] = mapped_column(String(16), default="mittel")  # niedrig|mittel|hoch
    status_kunde: Mapped[str] = mapped_column(String(64), default=KUNDENSTATUS[0])
    status_intern: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # Kein DB-FK auf angebote.id, um eine zyklische FK-Abhaengigkeit zwischen
    # anfragen und angebote (Angebot.anfrage_id) zu vermeiden.
    angebot_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

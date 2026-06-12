from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPKMixin
from src.core.status_codes import KUNDENSTATUS


class Bestellung(Base, UUIDPKMixin):
    __tablename__ = "bestellungen"

    bestell_nr: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    leistung_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leistungen.id"))
    besteller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    bestelldatum: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # status_kunde-Vokabular (KUNDENSTATUS) - eine Bestellung loest direkt eine
    # Signatur aus, daher kein anfrage_eingegangen/in_pruefung/angebot_erstellt.
    status: Mapped[str] = mapped_column(String(32), default=KUNDENSTATUS[3])  # "warten_auf_signatur"
    angebot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("angebote.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

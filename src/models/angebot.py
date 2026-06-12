from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPKMixin

# Angebotsstatus
ANGEBOT_ENTWURF = "entwurf"
ANGEBOT_BEREITGESTELLT = "bereitgestellt"
ANGEBOT_ANGENOMMEN = "angenommen"
ANGEBOT_ABGELEHNT = "abgelehnt"


class Angebot(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "angebote"

    angebotsnummer: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    anfrage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("anfragen.id"), nullable=True
    )
    leistung_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungen.id"), nullable=True
    )
    titel: Mapped[str] = mapped_column(String(255))
    gueltig_bis: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gesamtpreis: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), default=ANGEBOT_ENTWURF)

    positionen: Mapped[list["AngebotPosition"]] = relationship(
        back_populates="angebot", cascade="all, delete-orphan", order_by="AngebotPosition.sort_order"
    )


class AngebotPosition(Base, UUIDPKMixin):
    __tablename__ = "angebot_positionen"

    angebot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("angebote.id"))
    bezeichnung: Mapped[str] = mapped_column(String(255))
    menge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=1)
    einzelpreis: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    gesamtpreis: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    sort_order: Mapped[int] = mapped_column(default=0)

    angebot: Mapped["Angebot"] = relationship(back_populates="positionen")

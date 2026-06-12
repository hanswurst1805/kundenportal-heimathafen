from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPKMixin
from src.core.status_codes import KUNDENSTATUS

# Workshop
WORKSHOP_TYP_KICKOFF = "kickoff"
WORKSHOP_TYP_ONBOARDING = "onboarding"

WORKSHOP_GEPLANT = "geplant"
WORKSHOP_DURCHGEFUEHRT = "durchgefuehrt"
WORKSHOP_PROTOKOLL_FREIGEGEBEN = "protokoll_freigegeben"
WORKSHOP_VERSCHOBEN = "verschoben"

# Aufgabe
AUFGABE_OFFEN = "offen"
AUFGABE_IN_BEARBEITUNG = "in_bearbeitung"
AUFGABE_ERLEDIGT = "erledigt"
AUFGABE_BLOCKIERT = "blockiert"


class Leistungsschein(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "leistungsscheine"

    ls_nummer: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    auftrag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auftraege.id"), unique=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    leistung_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungen.id"), nullable=True
    )
    scope_beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verantwortlicher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    startdatum: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    kickoff_datum: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    workshop_datum: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    solltermin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status_kunde: Mapped[str] = mapped_column(String(64), default=KUNDENSTATUS[5])  # beauftragt
    status_intern: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    naechster_schritt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voraussetzungen: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    onboarding_ziele: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    onboarding_teilnehmer: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    onboarding_offene_punkte: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    abschlussstatus: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    aufgaben: Mapped[list["Aufgabe"]] = relationship(
        back_populates="leistungsschein", cascade="all, delete-orphan", order_by="Aufgabe.sort_order"
    )
    workshops: Mapped[list["Workshop"]] = relationship(
        back_populates="leistungsschein", cascade="all, delete-orphan"
    )


class Workshop(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "workshops"

    leistungsschein_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungsscheine.id")
    )
    typ: Mapped[str] = mapped_column(String(32))  # kickoff|onboarding
    termin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    teilnehmer: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    protokoll: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=WORKSHOP_GEPLANT)

    leistungsschein: Mapped["Leistungsschein"] = relationship(back_populates="workshops")


class Aufgabe(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "aufgaben"

    leistungsschein_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leistungsscheine.id")
    )
    titel: Mapped[str] = mapped_column(String(255))
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    zustaendigkeit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    faelligkeit: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=AUFGABE_OFFEN)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    leistungsschein: Mapped["Leistungsschein"] = relationship(back_populates="aufgaben")

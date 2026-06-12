from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPKMixin

# Akteurtypen
AKTEUR_USER = "user"
AKTEUR_SYSTEM = "system"
AKTEUR_ADAPTER = "adapter"


class Ereignisprotokoll(Base, UUIDPKMixin):
    """Revisions-/Statushistorie UND Trigger-Quelle fuer die Statusautomatisierung."""

    __tablename__ = "ereignisprotokoll"

    zeit: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    akteur_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    akteur_typ: Mapped[str] = mapped_column(String(16), default=AKTEUR_SYSTEM)
    ereignis_typ: Mapped[str] = mapped_column(String(64), index=True)
    bezugstyp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bezugs_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    vorher_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    nachher_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    verarbeitet: Mapped[bool] = mapped_column(Boolean, default=False)

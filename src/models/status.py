from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPKMixin
from src.core.status_codes import NOTIFY_OPTIONAL


class StatusRegel(Base, UUIDPKMixin, TimestampMixin):
    """Konfiguration der Trigger-Tabelle: Ereignis -> kundensichtbarer Status + Benachrichtigung."""

    __tablename__ = "status_regeln"

    ereignis_typ: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ziel_status_kunde: Mapped[str] = mapped_column(String(64))
    benachrichtigung: Mapped[str] = mapped_column(String(16), default=NOTIFY_OPTIONAL)  # ja|optional|nein
    aktiv: Mapped[bool] = mapped_column(Boolean, default=True)
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

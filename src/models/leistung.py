from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPKMixin


class Leistung(Base, UUIDPKMixin, TimestampMixin):
    """Katalog-Eintrag fuer eine bestellbare Standardleistung."""

    __tablename__ = "leistungen"

    leistungs_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    beschreibung: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kategorie: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preis: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    preiseinheit: Mapped[str] = mapped_column(String(32), default="einmalig")
    avv_erforderlich: Mapped[bool] = mapped_column(Boolean, default=False)
    ist_bestellbar: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from src.models.customer import Customer

# Rollen
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_KUNDE = "kunde"
ALL_ROLES = [ROLE_ADMIN, ROLE_USER, ROLE_KUNDE]


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=ROLE_KUNDE)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Zwei-Faktor-Authentifizierung (TOTP)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_required: Mapped[bool] = mapped_column(Boolean, default=False)
    backup_codes: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="users")

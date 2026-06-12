"""Erstellt beim ersten Start einen initialen Admin-Benutzer, falls noch keiner existiert."""

from __future__ import annotations

import logging

from sqlalchemy import func, select

from src.core.auth import hash_password
from src.core.config import settings
from src.core.database import get_async_session_factory
from src.models.user import ROLE_ADMIN, User

logger = logging.getLogger(__name__)


async def bootstrap_admin() -> None:
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        if count > 0:
            return

        admin = User(
            username="admin",
            password_hash=hash_password(settings.initial_admin_password),
            role=ROLE_ADMIN,
            display_name="Administrator",
            totp_required=True,
        )
        session.add(admin)
        await session.commit()
        logger.warning(
            "Initialer Admin-Benutzer 'admin' wurde angelegt. "
            "Bitte Passwort aendern und 2FA gemaess INITIAL_ADMIN_PASSWORD einrichten."
        )

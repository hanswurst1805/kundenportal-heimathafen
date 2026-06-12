"""Laedt die StatusRegel-Konfiguration (Trigger -> Zielstatus + Benachrichtigung)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.status import StatusRegel


async def get_status_regel(session: AsyncSession, ereignis_typ: str) -> Optional[StatusRegel]:
    result = await session.execute(select(StatusRegel).where(StatusRegel.ereignis_typ == ereignis_typ))
    return result.scalar_one_or_none()

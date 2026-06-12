"""Generiert einfache, fortlaufende Belegnummern (Demo-tauglich, nicht lueckenlos)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def next_number(session: AsyncSession, model, prefix: str) -> str:
    jahr = date.today().year
    count = (await session.execute(select(func.count()).select_from(model))).scalar_one()
    return f"{prefix}-{jahr}-{count + 1:04d}"

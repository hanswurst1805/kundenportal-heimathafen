"""Hilfsfunktionen, um vom Angebot zur urspruenglichen Anfrage oder Bestellung
zu navigieren und deren kundensichtbaren Status zu aktualisieren."""

from __future__ import annotations

from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.anfrage import Anfrage
from src.models.angebot import Angebot
from src.models.bestellung import Bestellung

Origin = Union[Anfrage, Bestellung]


async def find_origin_for_angebot(session: AsyncSession, angebot: Angebot) -> Optional[Origin]:
    if angebot.anfrage_id:
        return await session.get(Anfrage, angebot.anfrage_id)
    result = await session.execute(select(Bestellung).where(Bestellung.angebot_id == angebot.id))
    return result.scalar_one_or_none()


def set_origin_status(origin: Origin, status_kunde: str) -> None:
    if isinstance(origin, Anfrage):
        origin.status_kunde = status_kunde
    elif isinstance(origin, Bestellung):
        origin.status = status_kunde

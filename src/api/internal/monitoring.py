from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.core.status_codes import KUNDENSTATUS
from src.models.anfrage import Anfrage
from src.models.bestellung import Bestellung
from src.models.ereignis import Ereignisprotokoll
from src.models.leistungsschein import Leistungsschein
from src.schemas.ereignis import EreignisOut

router = APIRouter(
    prefix="/monitoring", tags=["intern-monitoring"], dependencies=[Depends(require_role("user", "admin"))]
)

OFFENE_STATUS = [
    s for s in KUNDENSTATUS if s not in ("abgeschlossen", "storniert")
]


class UebersichtResponse(BaseModel):
    offene_anfragen: int
    offene_bestellungen: int
    laufende_leistungsscheine: int
    unverarbeitete_ereignisse: int


@router.get("/uebersicht", response_model=UebersichtResponse)
async def uebersicht(session: AsyncSession = Depends(get_session)):
    anfragen = (
        await session.execute(
            select(func.count()).select_from(Anfrage).where(Anfrage.status_kunde.in_(OFFENE_STATUS))
        )
    ).scalar_one()
    bestellungen = (
        await session.execute(
            select(func.count()).select_from(Bestellung).where(Bestellung.status.in_(OFFENE_STATUS))
        )
    ).scalar_one()
    leistungsscheine = (
        await session.execute(
            select(func.count())
            .select_from(Leistungsschein)
            .where(Leistungsschein.status_kunde.in_(OFFENE_STATUS))
        )
    ).scalar_one()
    unverarbeitet = (
        await session.execute(
            select(func.count()).select_from(Ereignisprotokoll).where(Ereignisprotokoll.verarbeitet.is_(False))
        )
    ).scalar_one()

    return UebersichtResponse(
        offene_anfragen=anfragen,
        offene_bestellungen=bestellungen,
        laufende_leistungsscheine=leistungsscheine,
        unverarbeitete_ereignisse=unverarbeitet,
    )


@router.get("/ereignisse", response_model=list[EreignisOut])
async def list_ereignisse(
    verarbeitet: Optional[bool] = Query(default=None),
    ereignis_typ: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Ereignisprotokoll).order_by(Ereignisprotokoll.zeit.desc()).limit(limit)
    if verarbeitet is not None:
        stmt = stmt.where(Ereignisprotokoll.verarbeitet.is_(verarbeitet))
    if ereignis_typ:
        stmt = stmt.where(Ereignisprotokoll.ereignis_typ == ereignis_typ)
    result = await session.execute(stmt)
    return result.scalars().all()

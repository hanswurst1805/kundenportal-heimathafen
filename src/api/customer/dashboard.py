from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.anfrage import Anfrage
from src.models.bestellung import Bestellung
from src.models.leistungsschein import Leistungsschein
from src.schemas.anfrage import AnfrageOut
from src.schemas.bestellung import BestellungOut
from src.schemas.leistungsschein import LeistungsscheinKundenSicht

router = APIRouter(prefix="/dashboard", tags=["portal-dashboard"])

OFFENE_STATUS = {"warten_auf_signatur", "avv_ausstehend", "warten_auf_kunde"}


class DashboardResponse(BaseModel):
    offene_bestellungen: list[BestellungOut]
    offene_anfragen: list[AnfrageOut]
    laufende_leistungsscheine: list[LeistungsscheinKundenSicht]


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    bestellungen = (
        await session.execute(
            select(Bestellung).where(
                Bestellung.customer_id == ctx.customer_id, Bestellung.status.in_(OFFENE_STATUS)
            )
        )
    ).scalars().all()

    anfragen = (
        await session.execute(
            select(Anfrage).where(
                Anfrage.customer_id == ctx.customer_id, Anfrage.status_kunde.in_(OFFENE_STATUS)
            )
        )
    ).scalars().all()

    leistungsscheine = (
        await session.execute(
            select(Leistungsschein)
            .where(
                Leistungsschein.customer_id == ctx.customer_id,
                Leistungsschein.status_kunde.notin_(["abgeschlossen", "storniert"]),
            )
            .options(selectinload(Leistungsschein.aufgaben), selectinload(Leistungsschein.workshops))
        )
    ).scalars().all()

    return DashboardResponse(
        offene_bestellungen=bestellungen,
        offene_anfragen=anfragen,
        laufende_leistungsscheine=leistungsscheine,
    )

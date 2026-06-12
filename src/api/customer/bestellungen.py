from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_signature_provider
from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.bestellung import Bestellung
from src.models.leistung import Leistung
from src.models.signatur import BEZUG_BESTELLUNG
from src.schemas.bestellung import BestellungCreate, BestellungOut
from src.services.numbering import next_number

router = APIRouter(prefix="/bestellungen", tags=["portal-bestellungen"])


@router.get("", response_model=list[BestellungOut])
async def list_bestellungen(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Bestellung).where(Bestellung.customer_id == ctx.customer_id).order_by(Bestellung.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{bestellung_id}", response_model=BestellungOut)
async def get_bestellung(
    bestellung_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    bestellung = await session.get(Bestellung, bestellung_id)
    if not bestellung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(bestellung.customer_id)
    return bestellung


@router.post("", response_model=BestellungOut, status_code=status.HTTP_201_CREATED)
async def create_bestellung(
    data: BestellungCreate,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    leistung = await session.get(Leistung, data.leistung_id)
    if not leistung or not leistung.is_active or not leistung.ist_bestellbar:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leistung nicht verfuegbar")

    bestell_nr = await next_number(session, Bestellung, "BES")
    bestellung = Bestellung(
        bestell_nr=bestell_nr,
        customer_id=ctx.customer_id,
        leistung_id=leistung.id,
        besteller_id=ctx.user_id,
    )
    session.add(bestellung)
    await session.flush()

    await get_signature_provider().create_envelope(
        session, BEZUG_BESTELLUNG, bestellung.id, f"Beauftragung {leistung.name}"
    )

    return bestellung

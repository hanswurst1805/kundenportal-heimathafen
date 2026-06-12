from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.bestellung import Bestellung
from src.schemas.bestellung import BestellungOut

router = APIRouter(
    prefix="/bestellungen", tags=["intern-bestellungen"], dependencies=[Depends(require_role("user", "admin"))]
)


@router.get("", response_model=list[BestellungOut])
async def list_bestellungen(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Bestellung).order_by(Bestellung.created_at.desc()))
    return result.scalars().all()


@router.get("/{bestellung_id}", response_model=BestellungOut)
async def get_bestellung(bestellung_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    bestellung = await session.get(Bestellung, bestellung_id)
    if not bestellung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return bestellung

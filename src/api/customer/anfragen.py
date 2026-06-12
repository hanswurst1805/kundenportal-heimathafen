from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.anfrage import Anfrage
from src.schemas.anfrage import AnfrageCreate, AnfrageOut
from src.services.numbering import next_number

router = APIRouter(prefix="/anfragen", tags=["portal-anfragen"])


@router.get("", response_model=list[AnfrageOut])
async def list_anfragen(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Anfrage).where(Anfrage.customer_id == ctx.customer_id).order_by(Anfrage.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{anfrage_id}", response_model=AnfrageOut)
async def get_anfrage(
    anfrage_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    anfrage = await session.get(Anfrage, anfrage_id)
    if not anfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(anfrage.customer_id)
    return anfrage


@router.post("", response_model=AnfrageOut, status_code=status.HTTP_201_CREATED)
async def create_anfrage(
    data: AnfrageCreate,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    anfrage_nr = await next_number(session, Anfrage, "ANF")
    anfrage = Anfrage(
        anfrage_nr=anfrage_nr,
        customer_id=ctx.customer_id,
        ersteller_id=ctx.user_id,
        thema=data.thema,
        beschreibung=data.beschreibung,
        fachbereich=data.fachbereich,
        prioritaet=data.prioritaet,
    )
    session.add(anfrage)
    await session.flush()
    return anfrage

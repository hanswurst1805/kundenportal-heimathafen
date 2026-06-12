from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.leistungsschein import Leistungsschein
from src.schemas.leistungsschein import LeistungsscheinKundenSicht

router = APIRouter(prefix="/leistungsscheine", tags=["portal-leistungsscheine"])


@router.get("", response_model=list[LeistungsscheinKundenSicht])
async def list_leistungsscheine(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Leistungsschein)
        .where(Leistungsschein.customer_id == ctx.customer_id)
        .options(selectinload(Leistungsschein.aufgaben), selectinload(Leistungsschein.workshops))
        .order_by(Leistungsschein.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{leistungsschein_id}", response_model=LeistungsscheinKundenSicht)
async def get_leistungsschein(
    leistungsschein_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Leistungsschein)
        .where(Leistungsschein.id == leistungsschein_id)
        .options(selectinload(Leistungsschein.aufgaben), selectinload(Leistungsschein.workshops))
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(ls.customer_id)
    return ls

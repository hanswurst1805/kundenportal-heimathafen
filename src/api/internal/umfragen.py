from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.umfrage import Umfrage
from src.schemas.umfrage import UmfrageOut

router = APIRouter(prefix="/umfragen", tags=["intern-umfragen"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[UmfrageOut])
async def list_umfragen(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Umfrage).order_by(Umfrage.created_at.desc()))
    return result.scalars().all()


@router.get("/{umfrage_id}", response_model=UmfrageOut)
async def get_umfrage(umfrage_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    umfrage = await session.get(Umfrage, umfrage_id)
    if not umfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return umfrage

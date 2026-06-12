from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.umfrage import UMFRAGE_BEANTWORTET, Umfrage
from src.schemas.umfrage import UmfrageAntwort, UmfrageOut

router = APIRouter(prefix="/umfragen", tags=["portal-umfragen"])


@router.get("", response_model=list[UmfrageOut])
async def list_umfragen(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Umfrage).where(Umfrage.customer_id == ctx.customer_id).order_by(Umfrage.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{umfrage_id}/beantworten", response_model=UmfrageOut)
async def beantworten(
    umfrage_id: uuid.UUID,
    data: UmfrageAntwort,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    umfrage = await session.get(Umfrage, umfrage_id)
    if not umfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(umfrage.customer_id)

    umfrage.bewertung = data.bewertung
    umfrage.kommentar = data.kommentar
    umfrage.status = UMFRAGE_BEANTWORTET
    umfrage.beantwortet_am = datetime.now(timezone.utc)
    return umfrage

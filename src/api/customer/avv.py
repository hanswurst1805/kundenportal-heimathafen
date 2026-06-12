from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.automation.events import publish
from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.core.status_codes import EVENT_AVV_COMPLETED
from src.models.avv import AVV, AVV_AUSSTEHEND
from src.models.ereignis import AKTEUR_USER
from src.schemas.avv import AVVOut

router = APIRouter(prefix="/avv", tags=["portal-avv"])


@router.get("", response_model=list[AVVOut])
async def list_avv(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(select(AVV).where(AVV.customer_id == ctx.customer_id))
    return result.scalars().all()


@router.post("/{avv_id}/annehmen", response_model=AVVOut)
async def annehmen(
    avv_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    avv = await session.get(AVV, avv_id)
    if not avv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(avv.customer_id)
    if avv.status != AVV_AUSSTEHEND:
        raise HTTPException(status.HTTP_409_CONFLICT, "AVV ist nicht offen")

    await publish(
        session,
        EVENT_AVV_COMPLETED,
        customer_id=avv.customer_id,
        bezugstyp="avv",
        bezugs_id=avv.id,
        akteur_id=ctx.user_id,
        akteur_typ=AKTEUR_USER,
    )
    return avv

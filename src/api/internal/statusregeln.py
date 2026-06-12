from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.status import StatusRegel
from src.schemas.status import StatusRegelOut, StatusRegelUpdate

router = APIRouter(
    prefix="/statusregeln", tags=["intern-statusregeln"], dependencies=[Depends(require_role("admin"))]
)


@router.get("", response_model=list[StatusRegelOut])
async def list_statusregeln(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(StatusRegel).order_by(StatusRegel.ereignis_typ))
    return result.scalars().all()


@router.patch("/{regel_id}", response_model=StatusRegelOut)
async def update_statusregel(
    regel_id: uuid.UUID, data: StatusRegelUpdate, session: AsyncSession = Depends(get_session)
):
    regel = await session.get(StatusRegel, regel_id)
    if not regel:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(regel, field, value)
    return regel

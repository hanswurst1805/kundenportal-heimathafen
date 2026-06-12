from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.adapters.registry import get_signature_provider
from src.core.auth import require_role
from src.core.database import get_session
from src.models.angebot import ANGEBOT_BEREITGESTELLT, ANGEBOT_ENTWURF, Angebot
from src.models.signatur import BEZUG_ANGEBOT
from src.schemas.angebot import AngebotOut
from src.services.origin import find_origin_for_angebot, set_origin_status

router = APIRouter(prefix="/angebote", tags=["intern-angebote"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[AngebotOut])
async def list_angebote(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).options(selectinload(Angebot.positionen)).order_by(Angebot.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{angebot_id}", response_model=AngebotOut)
async def get_angebot(angebot_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
    )
    angebot = result.scalar_one_or_none()
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return angebot


@router.post("/{angebot_id}/bereitstellen", response_model=AngebotOut)
async def bereitstellen(angebot_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot_id).options(selectinload(Angebot.positionen))
    )
    angebot = result.scalar_one_or_none()
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if angebot.status != ANGEBOT_ENTWURF:
        raise HTTPException(status.HTTP_409_CONFLICT, "Angebot kann in diesem Status nicht bereitgestellt werden")

    angebot.status = ANGEBOT_BEREITGESTELLT

    origin = await find_origin_for_angebot(session, angebot)
    if origin:
        set_origin_status(origin, "warten_auf_signatur")

    await get_signature_provider().create_envelope(session, BEZUG_ANGEBOT, angebot.id, angebot.titel)

    return angebot

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.registry import get_signature_provider
from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.angebot import ANGEBOT_ABGELEHNT, ANGEBOT_BEREITGESTELLT, Angebot
from src.models.signatur import BEZUG_ANGEBOT, Signaturvorgang
from src.schemas.angebot import AngebotAblehnenRequest, AngebotOut
from src.services.origin import find_origin_for_angebot, set_origin_status

router = APIRouter(prefix="/angebote", tags=["portal-angebote"])


@router.get("", response_model=list[AngebotOut])
async def list_angebote(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Angebot).where(Angebot.customer_id == ctx.customer_id).order_by(Angebot.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{angebot_id}", response_model=AngebotOut)
async def get_angebot(
    angebot_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    angebot = await session.get(Angebot, angebot_id)
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(angebot.customer_id)
    return angebot


@router.post("/{angebot_id}/ablehnen", response_model=AngebotOut)
async def ablehnen(
    angebot_id: uuid.UUID,
    data: AngebotAblehnenRequest,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    angebot = await session.get(Angebot, angebot_id)
    if not angebot:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(angebot.customer_id)
    if angebot.status != ANGEBOT_BEREITGESTELLT:
        raise HTTPException(status.HTTP_409_CONFLICT, "Angebot kann in diesem Status nicht abgelehnt werden")

    angebot.status = ANGEBOT_ABGELEHNT

    vorgang = (
        await session.execute(
            select(Signaturvorgang)
            .where(Signaturvorgang.bezugstyp == BEZUG_ANGEBOT, Signaturvorgang.bezugs_id == angebot.id)
            .order_by(Signaturvorgang.created_at.desc())
        )
    ).scalars().first()
    if vorgang:
        await get_signature_provider().cancel(session, vorgang)

    origin = await find_origin_for_angebot(session, angebot)
    if origin:
        set_origin_status(origin, "storniert")

    return angebot

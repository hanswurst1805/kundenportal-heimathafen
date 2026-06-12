from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.auftrag import Auftrag, Auftragsbestaetigung
from src.schemas.auftrag import AuftragOut, AuftragsbestaetigungOut

router = APIRouter(prefix="/auftraege", tags=["portal-auftraege"])


@router.get("", response_model=list[AuftragOut])
async def list_auftraege(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Auftrag).where(Auftrag.customer_id == ctx.customer_id).order_by(Auftrag.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{auftrag_id}", response_model=AuftragOut)
async def get_auftrag(
    auftrag_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    auftrag = await session.get(Auftrag, auftrag_id)
    if not auftrag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(auftrag.customer_id)
    return auftrag


@router.get("/{auftrag_id}/auftragsbestaetigung", response_model=AuftragsbestaetigungOut)
async def get_auftragsbestaetigung(
    auftrag_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    auftrag = await session.get(Auftrag, auftrag_id)
    if not auftrag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(auftrag.customer_id)

    bestaetigung = (
        await session.execute(
            select(Auftragsbestaetigung).where(Auftragsbestaetigung.auftrag_id == auftrag.id)
        )
    ).scalar_one_or_none()
    if not bestaetigung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return bestaetigung


@router.post("/{auftrag_id}/auftragsbestaetigung/kenntnisnahme", response_model=AuftragsbestaetigungOut)
async def kenntnisnahme(
    auftrag_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    auftrag = await session.get(Auftrag, auftrag_id)
    if not auftrag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(auftrag.customer_id)

    bestaetigung = (
        await session.execute(
            select(Auftragsbestaetigung).where(Auftragsbestaetigung.auftrag_id == auftrag.id)
        )
    ).scalar_one_or_none()
    if not bestaetigung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Keine Auftragsbestaetigung vorhanden")

    bestaetigung.kenntnisnahme_am = datetime.now(timezone.utc)
    return bestaetigung

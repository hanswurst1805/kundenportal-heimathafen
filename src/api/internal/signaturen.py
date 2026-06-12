from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.signatur import (
    SIGNATUR_ABGELAUFEN,
    SIGNATUR_ABGELEHNT,
    SIGNATUR_FEHLER,
    SIGNATUR_VERSENDET,
    Signaturvorgang,
)
from src.schemas.signatur import SignaturvorgangOut

router = APIRouter(
    prefix="/signaturen", tags=["intern-signaturen"], dependencies=[Depends(require_role("user", "admin"))]
)


@router.get("", response_model=list[SignaturvorgangOut])
async def list_signaturvorgaenge(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Signaturvorgang).order_by(Signaturvorgang.created_at.desc()))
    return result.scalars().all()


@router.get("/{vorgang_id}", response_model=SignaturvorgangOut)
async def get_signaturvorgang(vorgang_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    vorgang = await session.get(Signaturvorgang, vorgang_id)
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return vorgang


@router.post("/{vorgang_id}/erinnerung", response_model=SignaturvorgangOut)
async def erinnerung(vorgang_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    vorgang = await session.get(Signaturvorgang, vorgang_id)
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if vorgang.status != SIGNATUR_VERSENDET:
        raise HTTPException(status.HTTP_409_CONFLICT, "Signaturvorgang ist nicht offen")
    vorgang.erinnerung_gesendet_am = datetime.now(timezone.utc)
    return vorgang


@router.post("/{vorgang_id}/retry", response_model=SignaturvorgangOut)
async def retry(vorgang_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    vorgang = await session.get(Signaturvorgang, vorgang_id)
    if not vorgang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    if vorgang.status not in (SIGNATUR_FEHLER, SIGNATUR_ABGELAUFEN, SIGNATUR_ABGELEHNT):
        raise HTTPException(status.HTTP_409_CONFLICT, "Signaturvorgang kann nicht erneut versendet werden")
    vorgang.status = SIGNATUR_VERSENDET
    vorgang.versandzeit = datetime.now(timezone.utc)
    vorgang.erinnerung_gesendet_am = None
    return vorgang

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import AuthContext, require_customer
from src.core.database import get_session
from src.models.dokument import SICHTBAR_KUNDE, Dokument
from src.schemas.dokument import DokumentOut

router = APIRouter(prefix="/dokumente", tags=["portal-dokumente"])


@router.get("", response_model=list[DokumentOut])
async def list_dokumente(
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    result = await session.execute(
        select(Dokument)
        .where(Dokument.customer_id == ctx.customer_id, Dokument.sichtbarkeit == SICHTBAR_KUNDE)
        .order_by(Dokument.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{dokument_id}/download")
async def download_dokument(
    dokument_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_customer),
):
    dokument = await session.get(Dokument, dokument_id)
    if not dokument or dokument.sichtbarkeit != SICHTBAR_KUNDE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    ctx.require_customer_scope(dokument.customer_id)

    pfad = Path(dokument.ablageort)
    if not pfad.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Datei nicht verfuegbar")
    return FileResponse(pfad, filename=dokument.dateiname, media_type="application/pdf")

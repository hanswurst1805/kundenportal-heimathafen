from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.dokument import Dokument
from src.schemas.dokument import DokumentOut

router = APIRouter(
    prefix="/dokumente", tags=["intern-dokumente"], dependencies=[Depends(require_role("user", "admin"))]
)


@router.get("", response_model=list[DokumentOut])
async def list_dokumente(
    bezugstyp: Optional[str] = None,
    bezugs_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_session),
):
    """Interne Dokumentenliste (alle Mandanten), optional gefiltert."""
    stmt = select(Dokument).order_by(Dokument.created_at.desc())
    if bezugstyp:
        stmt = stmt.where(Dokument.bezugstyp == bezugstyp)
    if bezugs_id:
        stmt = stmt.where(Dokument.bezugs_id == bezugs_id)
    if customer_id:
        stmt = stmt.where(Dokument.customer_id == customer_id)
    return (await session.execute(stmt)).scalars().all()


@router.get("/{dokument_id}/download")
async def download_dokument(
    dokument_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    dokument = await session.get(Dokument, dokument_id)
    if not dokument:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    pfad = Path(dokument.ablageort)
    if not pfad.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Datei nicht verfuegbar")
    return FileResponse(pfad, filename=dokument.dateiname, media_type="application/pdf")

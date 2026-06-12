from __future__ import annotations

from fastapi import APIRouter, Depends
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

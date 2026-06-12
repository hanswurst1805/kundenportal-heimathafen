from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_customer
from src.core.database import get_session
from src.models.leistung import Leistung
from src.schemas.catalog import LeistungOut

router = APIRouter(prefix="/leistungen", tags=["portal-katalog"])


@router.get("", response_model=list[LeistungOut])
async def list_leistungen(
    session: AsyncSession = Depends(get_session),
    _ctx=Depends(require_customer),
):
    result = await session.execute(
        select(Leistung).where(Leistung.is_active.is_(True), Leistung.ist_bestellbar.is_(True))
    )
    return result.scalars().all()

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.avv import AVV, AVVVorlage
from src.schemas.avv import AVVOut, AVVVorlageCreate, AVVVorlageOut, AVVVorlageUpdate

router = APIRouter(prefix="/avv", tags=["intern-avv"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[AVVOut])
async def list_avv(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AVV).order_by(AVV.created_at.desc()))
    return result.scalars().all()


@router.get("/{avv_id}", response_model=AVVOut)
async def get_avv(avv_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    avv = await session.get(AVV, avv_id)
    if not avv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return avv


# ---------------------------------------------------------------------------
# AVV-Vorlagenverwaltung (admin-only)
# ---------------------------------------------------------------------------

vorlagen_router = APIRouter(
    prefix="/avv-vorlagen", tags=["intern-avv-vorlagen"], dependencies=[Depends(require_role("admin"))]
)


@vorlagen_router.get("", response_model=list[AVVVorlageOut])
async def list_vorlagen(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AVVVorlage).order_by(AVVVorlage.created_at.desc()))
    return result.scalars().all()


@vorlagen_router.post("", response_model=AVVVorlageOut, status_code=status.HTTP_201_CREATED)
async def create_vorlage(data: AVVVorlageCreate, session: AsyncSession = Depends(get_session)):
    vorlage = AVVVorlage(**data.model_dump())
    session.add(vorlage)
    await session.flush()
    return vorlage


@vorlagen_router.patch("/{vorlage_id}", response_model=AVVVorlageOut)
async def update_vorlage(
    vorlage_id: uuid.UUID, data: AVVVorlageUpdate, session: AsyncSession = Depends(get_session)
):
    vorlage = await session.get(AVVVorlage, vorlage_id)
    if not vorlage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vorlage, field, value)
    return vorlage

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.leistung import Leistung
from src.schemas.catalog import LeistungCreate, LeistungOut, LeistungUpdate

router = APIRouter(
    prefix="/leistungen", tags=["intern-leistungen"], dependencies=[Depends(require_role("user", "admin"))]
)


@router.get("", response_model=list[LeistungOut])
async def list_leistungen(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Leistung).order_by(Leistung.name))
    return result.scalars().all()


@router.get("/{leistung_id}", response_model=LeistungOut)
async def get_leistung(leistung_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    leistung = await session.get(Leistung, leistung_id)
    if not leistung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return leistung


@router.post("", response_model=LeistungOut, status_code=status.HTTP_201_CREATED)
async def create_leistung(data: LeistungCreate, session: AsyncSession = Depends(get_session)):
    leistung = Leistung(**data.model_dump())
    session.add(leistung)
    await session.flush()
    return leistung


@router.patch("/{leistung_id}", response_model=LeistungOut)
async def update_leistung(
    leistung_id: uuid.UUID, data: LeistungUpdate, session: AsyncSession = Depends(get_session)
):
    leistung = await session.get(Leistung, leistung_id)
    if not leistung:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(leistung, field, value)
    return leistung

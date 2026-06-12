from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.automation.events import publish
from src.core.auth import AuthContext, require_role
from src.core.database import get_session
from src.core.status_codes import (
    EVENT_CUSTOMER_INPUT_REQUIRED,
    EVENT_DELIVERY_COMPLETED,
)
from src.models.ereignis import AKTEUR_USER
from src.models.leistungsschein import Aufgabe, Leistungsschein
from src.schemas.leistungsschein import (
    AufgabeCreate,
    AufgabeOut,
    AufgabeUpdate,
    LeistungsscheinInternSicht,
    LeistungsscheinInternUpdate,
)

router = APIRouter(
    prefix="/leistungsscheine",
    tags=["intern-leistungsscheine"],
    dependencies=[Depends(require_role("user", "admin"))],
)


def _options():
    return (selectinload(Leistungsschein.aufgaben), selectinload(Leistungsschein.workshops))


@router.get("", response_model=list[LeistungsscheinInternSicht])
async def list_leistungsscheine(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Leistungsschein).options(*_options()).order_by(Leistungsschein.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{leistungsschein_id}", response_model=LeistungsscheinInternSicht)
async def get_leistungsschein(leistungsschein_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Leistungsschein).where(Leistungsschein.id == leistungsschein_id).options(*_options())
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return ls


@router.patch("/{leistungsschein_id}", response_model=LeistungsscheinInternSicht)
async def update_leistungsschein(
    leistungsschein_id: uuid.UUID, data: LeistungsscheinInternUpdate, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Leistungsschein).where(Leistungsschein.id == leistungsschein_id).options(*_options())
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ls, field, value)
    return ls


@router.post("/{leistungsschein_id}/kundenrueckfrage", response_model=LeistungsscheinInternSicht)
async def kundenrueckfrage(
    leistungsschein_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_role("user", "admin")),
):
    result = await session.execute(
        select(Leistungsschein).where(Leistungsschein.id == leistungsschein_id).options(*_options())
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    await publish(
        session,
        EVENT_CUSTOMER_INPUT_REQUIRED,
        customer_id=ls.customer_id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        akteur_id=ctx.user_id,
        akteur_typ=AKTEUR_USER,
    )
    return ls


@router.post("/{leistungsschein_id}/abschliessen", response_model=LeistungsscheinInternSicht)
async def abschliessen(
    leistungsschein_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    ctx: AuthContext = Depends(require_role("user", "admin")),
):
    result = await session.execute(
        select(Leistungsschein).where(Leistungsschein.id == leistungsschein_id).options(*_options())
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    await publish(
        session,
        EVENT_DELIVERY_COMPLETED,
        customer_id=ls.customer_id,
        bezugstyp="leistungsschein",
        bezugs_id=ls.id,
        akteur_id=ctx.user_id,
        akteur_typ=AKTEUR_USER,
    )
    return ls


# ---------------------------------------------------------------------------
# Aufgaben
# ---------------------------------------------------------------------------


@router.get("/{leistungsschein_id}/aufgaben", response_model=list[AufgabeOut])
async def list_aufgaben(leistungsschein_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Aufgabe)
        .where(Aufgabe.leistungsschein_id == leistungsschein_id)
        .order_by(Aufgabe.sort_order)
    )
    return result.scalars().all()


@router.post("/{leistungsschein_id}/aufgaben", response_model=AufgabeOut, status_code=status.HTTP_201_CREATED)
async def create_aufgabe(
    leistungsschein_id: uuid.UUID, data: AufgabeCreate, session: AsyncSession = Depends(get_session)
):
    ls = await session.get(Leistungsschein, leistungsschein_id)
    if not ls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    aufgabe = Aufgabe(leistungsschein_id=ls.id, **data.model_dump())
    session.add(aufgabe)
    await session.flush()
    return aufgabe


@router.patch("/{leistungsschein_id}/aufgaben/{aufgabe_id}", response_model=AufgabeOut)
async def update_aufgabe(
    leistungsschein_id: uuid.UUID,
    aufgabe_id: uuid.UUID,
    data: AufgabeUpdate,
    session: AsyncSession = Depends(get_session),
):
    aufgabe = await session.get(Aufgabe, aufgabe_id)
    if not aufgabe or aufgabe.leistungsschein_id != leistungsschein_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(aufgabe, field, value)
    return aufgabe


@router.delete("/{leistungsschein_id}/aufgaben/{aufgabe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aufgabe(
    leistungsschein_id: uuid.UUID, aufgabe_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    aufgabe = await session.get(Aufgabe, aufgabe_id)
    if not aufgabe or aufgabe.leistungsschein_id != leistungsschein_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    await session.delete(aufgabe)

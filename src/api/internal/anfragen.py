from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.auth import require_role
from src.core.database import get_session
from src.core.status_codes import KUNDENSTATUS
from src.models.anfrage import Anfrage
from src.models.angebot import Angebot, AngebotPosition
from src.schemas.anfrage import AnfrageInternOut, AnfrageInternUpdate
from src.schemas.angebot import AngebotCreate, AngebotOut
from src.services.numbering import next_number

router = APIRouter(prefix="/anfragen", tags=["intern-anfragen"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[AnfrageInternOut])
async def list_anfragen(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Anfrage).order_by(Anfrage.created_at.desc()))
    return result.scalars().all()


@router.get("/{anfrage_id}", response_model=AnfrageInternOut)
async def get_anfrage(anfrage_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    anfrage = await session.get(Anfrage, anfrage_id)
    if not anfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return anfrage


@router.patch("/{anfrage_id}", response_model=AnfrageInternOut)
async def update_anfrage(
    anfrage_id: uuid.UUID, data: AnfrageInternUpdate, session: AsyncSession = Depends(get_session)
):
    anfrage = await session.get(Anfrage, anfrage_id)
    if not anfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(anfrage, field, value)
    return anfrage


@router.post("/{anfrage_id}/angebot", response_model=AngebotOut, status_code=status.HTTP_201_CREATED)
async def create_angebot_fuer_anfrage(
    anfrage_id: uuid.UUID, data: AngebotCreate, session: AsyncSession = Depends(get_session)
):
    anfrage = await session.get(Anfrage, anfrage_id)
    if not anfrage:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    angebotsnummer = await next_number(session, Angebot, "ANG")
    angebot = Angebot(
        angebotsnummer=angebotsnummer,
        customer_id=anfrage.customer_id,
        anfrage_id=anfrage.id,
        leistung_id=data.leistung_id,
        titel=data.titel,
        gueltig_bis=data.gueltig_bis,
    )
    session.add(angebot)
    await session.flush()

    gesamtpreis = 0
    for pos in data.positionen:
        positionspreis = pos.menge * pos.einzelpreis
        session.add(
            AngebotPosition(
                angebot_id=angebot.id,
                bezeichnung=pos.bezeichnung,
                menge=pos.menge,
                einzelpreis=pos.einzelpreis,
                gesamtpreis=positionspreis,
                sort_order=pos.sort_order,
            )
        )
        gesamtpreis += positionspreis
    angebot.gesamtpreis = gesamtpreis

    anfrage.angebot_id = angebot.id
    anfrage.status_kunde = KUNDENSTATUS[2]  # angebot_erstellt
    anfrage.status_intern = "kalkulation_in_erstellung"
    await session.flush()

    result = await session.execute(
        select(Angebot).where(Angebot.id == angebot.id).options(selectinload(Angebot.positionen))
    )
    return result.scalar_one()
